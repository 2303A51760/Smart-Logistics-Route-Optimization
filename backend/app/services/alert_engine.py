import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal, check_db_connection
from app.core.redis import publish_tracking_event
from app.core.logistics_store import (
    SEED_VEHICLES,
    SEED_DRIVERS,
    SEED_ORDERS,
    SEED_ROUTES,
    SEED_ROUTE_STOPS,
    SEED_VEHICLE_MAINTENANCE,
    SEED_NOTIFICATIONS,
)
from app.models.user import UserRole
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver, DriverStatus
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.route import Route, RouteStop, RouteStatus, RouteStopStatus
from app.models.maintenance import VehicleMaintenance, MaintenanceStatus
from app.models.notification import Notification, AlertType, AlertSeverity

logger = logging.getLogger(__name__)

MAX_ROUTE_DISTANCE_THRESHOLD_KM = 100.0


class IntelligentAlertEngine:
    """
    Evaluates real-time telemetry, fleet state, routing limits, maintenance schedules,
    and order deadlines to generate actionable intelligent logistics alerts.
    """

    async def evaluate_and_generate_alerts(self, db_session=None) -> List[dict]:
        """
        Runs comprehensive evaluation across all 6 core logistics hazard categories.
        Returns list of newly generated alert dicts.
        """
        alerts: List[dict] = []
        is_db_alive = await check_db_connection()

        if is_db_alive and db_session:
            try:
                db_alerts = await self._evaluate_db_rules(db_session)
                alerts.extend(db_alerts)
            except Exception as e:
                logger.error(f"Error evaluating alerts in DB: {e}")
                mem_alerts = self._evaluate_in_memory_rules()
                alerts.extend(mem_alerts)
        else:
            mem_alerts = self._evaluate_in_memory_rules()
            alerts.extend(mem_alerts)

        # Broadcast each alert via WebSocket and Redis
        for alert in alerts:
            await self._broadcast_alert(alert)

        return alerts

    def _evaluate_in_memory_rules(self) -> List[dict]:
        generated = []
        now = datetime.utcnow()

        # 1. MAINTENANCE DUE
        for veh_id, veh in SEED_VEHICLES.items():
            curr_mileage = float(veh.get("mileage", 0.0))
            veh_num = veh.get("vehicle_number", veh_id)
            driver_id = veh.get("driver_id")

            # Check latest maintenance
            latest_next_mileage = None
            for maint in SEED_VEHICLE_MAINTENANCE.values():
                if maint.get("vehicle_id") == veh_id and maint.get("status") == "COMPLETED":
                    next_m = float(maint.get("next_maintenance_mileage", 0.0))
                    if latest_next_mileage is None or next_m > latest_next_mileage:
                        latest_next_mileage = next_m

            is_overdue = False
            if latest_next_mileage and curr_mileage >= latest_next_mileage:
                is_overdue = True
            elif veh.get("status") == "MAINTENANCE":
                is_overdue = True

            if is_overdue:
                alert_dict = {
                    "id": f"notif-{uuid.uuid4().hex[:8]}",
                    "recipient_user_id": None,
                    "recipient_role": "ADMIN",
                    "driver_id": driver_id,
                    "vehicle_id": veh_id,
                    "route_id": None,
                    "order_id": None,
                    "title": f"Maintenance Required: Vehicle {veh_num}",
                    "message": f"Vehicle {veh_num} has exceeded service interval (Odometer: {curr_mileage:.1f} km, Due: {latest_next_mileage or 0:.1f} km).",
                    "alert_type": AlertType.MAINTENANCE_DUE.value,
                    "severity": AlertSeverity.CRITICAL.value if curr_mileage >= (latest_next_mileage or 0) else AlertSeverity.WARNING.value,
                    "is_read": False,
                    "read_at": None,
                    "created_at": now,
                }
                SEED_NOTIFICATIONS[alert_dict["id"]] = alert_dict
                generated.append(alert_dict)

        # 2. VEHICLE OVERLOADED
        for veh_id, veh in SEED_VEHICLES.items():
            capacity = float(veh.get("capacity", 1000.0))
            veh_num = veh.get("vehicle_number", veh_id)
            driver_id = veh.get("driver_id")

            # Calculate total payload for orders assigned to this vehicle / driver
            total_weight = 0.0
            if driver_id:
                for ord_item in SEED_ORDERS.values():
                    if ord_item.get("assigned_driver_id") == driver_id and ord_item.get("status") in ["ASSIGNED", "OUT_FOR_DELIVERY"]:
                        total_weight += float(ord_item.get("package_weight", 0.0))

            if total_weight > capacity:
                alert_dict = {
                    "id": f"notif-{uuid.uuid4().hex[:8]}",
                    "recipient_user_id": None,
                    "recipient_role": "LOGISTICS_MANAGER",
                    "driver_id": driver_id,
                    "vehicle_id": veh_id,
                    "route_id": None,
                    "order_id": None,
                    "title": f"Vehicle Overload: {veh_num}",
                    "message": f"Vehicle {veh_num} payload of {total_weight:.1f} kg exceeds rated capacity of {capacity:.1f} kg.",
                    "alert_type": AlertType.VEHICLE_OVERLOADED.value,
                    "severity": AlertSeverity.CRITICAL.value,
                    "is_read": False,
                    "read_at": None,
                    "created_at": now,
                }
                SEED_NOTIFICATIONS[alert_dict["id"]] = alert_dict
                generated.append(alert_dict)

        # 3. DRIVER UNAVAILABLE
        for drv_id, drv in SEED_DRIVERS.items():
            drv_status = drv.get("status", "AVAILABLE")
            drv_name = drv.get("name", drv_id)
            if drv_status in ["OFF_DUTY", "INACTIVE"]:
                # Check if this driver is assigned to active routes or orders
                has_active = any(
                    ord_item.get("assigned_driver_id") == drv_id and ord_item.get("status") in ["ASSIGNED", "OUT_FOR_DELIVERY"]
                    for ord_item in SEED_ORDERS.values()
                )
                if has_active:
                    alert_dict = {
                        "id": f"notif-{uuid.uuid4().hex[:8]}",
                        "recipient_user_id": None,
                        "recipient_role": "LOGISTICS_MANAGER",
                        "driver_id": drv_id,
                        "vehicle_id": None,
                        "route_id": None,
                        "order_id": None,
                        "title": f"Driver Unavailable: {drv_name}",
                        "message": f"Driver {drv_name} has active deliveries assigned but is currently marked {drv_status}.",
                        "alert_type": AlertType.DRIVER_UNAVAILABLE.value,
                        "severity": AlertSeverity.WARNING.value,
                        "is_read": False,
                        "read_at": None,
                        "created_at": now,
                    }
                    SEED_NOTIFICATIONS[alert_dict["id"]] = alert_dict
                    generated.append(alert_dict)

        # 4. DELIVERY DELAYED
        for ord_id, ord_item in SEED_ORDERS.items():
            if ord_item.get("status") in ["ASSIGNED", "OUT_FOR_DELIVERY", "PENDING"]:
                window_end = ord_item.get("delivery_window_end")
                if window_end and now > window_end:
                    alert_dict = {
                        "id": f"notif-{uuid.uuid4().hex[:8]}",
                        "recipient_user_id": None,
                        "recipient_role": "LOGISTICS_MANAGER",
                        "driver_id": ord_item.get("assigned_driver_id"),
                        "vehicle_id": None,
                        "route_id": None,
                        "order_id": ord_id,
                        "title": f"Delivery Delayed: Order {ord_item.get('order_number')}",
                        "message": f"Order {ord_item.get('order_number')} has missed its scheduled delivery deadline ({window_end.strftime('%H:%M')}).",
                        "alert_type": AlertType.DELIVERY_DELAYED.value,
                        "severity": AlertSeverity.WARNING.value,
                        "is_read": False,
                        "read_at": None,
                        "created_at": now,
                    }
                    SEED_NOTIFICATIONS[alert_dict["id"]] = alert_dict
                    generated.append(alert_dict)

        # 5. ROUTE EXCEEDS MAXIMUM DISTANCE
        for rt_id, rt in SEED_ROUTES.items():
            tot_dist = float(rt.get("total_distance", 0.0))
            if tot_dist > MAX_ROUTE_DISTANCE_THRESHOLD_KM:
                alert_dict = {
                    "id": f"notif-{uuid.uuid4().hex[:8]}",
                    "recipient_user_id": None,
                    "recipient_role": "LOGISTICS_MANAGER",
                    "driver_id": rt.get("driver_id"),
                    "vehicle_id": rt.get("vehicle_id"),
                    "route_id": rt_id,
                    "order_id": None,
                    "title": f"Route Distance Alert: {rt.get('name')}",
                    "message": f"Route {rt.get('name')} exceeds maximum optimal limit of {MAX_ROUTE_DISTANCE_THRESHOLD_KM:.0f} km (Current: {tot_dist:.1f} km).",
                    "alert_type": AlertType.ROUTE_EXCEEDS_MAX_DISTANCE.value,
                    "severity": AlertSeverity.WARNING.value,
                    "is_read": False,
                    "read_at": None,
                    "created_at": now,
                }
                SEED_NOTIFICATIONS[alert_dict["id"]] = alert_dict
                generated.append(alert_dict)

        # 6. URGENT ORDER NOT ASSIGNED
        for ord_id, ord_item in SEED_ORDERS.items():
            if ord_item.get("priority") in ["URGENT", "HIGH"] and ord_item.get("status") == "PENDING" and not ord_item.get("assigned_driver_id"):
                alert_dict = {
                    "id": f"notif-{uuid.uuid4().hex[:8]}",
                    "recipient_user_id": None,
                    "recipient_role": "LOGISTICS_MANAGER",
                    "driver_id": None,
                    "vehicle_id": None,
                    "route_id": None,
                    "order_id": ord_id,
                    "title": f"Urgent Order Unassigned: {ord_item.get('order_number')}",
                    "message": f"High-priority order {ord_item.get('order_number')} is currently unassigned in PENDING queue.",
                    "alert_type": AlertType.URGENT_ORDER_UNASSIGNED.value,
                    "severity": AlertSeverity.CRITICAL.value if ord_item.get("priority") == "URGENT" else AlertSeverity.WARNING.value,
                    "is_read": False,
                    "read_at": None,
                    "created_at": now,
                }
                SEED_NOTIFICATIONS[alert_dict["id"]] = alert_dict
                generated.append(alert_dict)

        return generated

    async def _evaluate_db_rules(self, db_session) -> List[dict]:
        generated = []
        now = datetime.utcnow()

        # Fetch vehicles and maintenance
        res_v = await db_session.execute(select(Vehicle).options(selectinload(Vehicle.maintenance_records)))
        vehicles = res_v.scalars().all()

        # 1. MAINTENANCE DUE
        for veh in vehicles:
            curr_mileage = float(veh.mileage or 0.0)
            latest_next = 0.0
            if veh.maintenance_records:
                for rec in veh.maintenance_records:
                    if rec.status == MaintenanceStatus.COMPLETED.value and rec.next_maintenance_mileage > latest_next:
                        latest_next = float(rec.next_maintenance_mileage)

            is_due = (latest_next > 0 and curr_mileage >= latest_next) or veh.status == VehicleStatus.MAINTENANCE.value
            if is_due:
                notif = Notification(
                    recipient_role="ADMIN",
                    driver_id=veh.driver_id,
                    vehicle_id=veh.id,
                    title=f"Maintenance Required: Vehicle {veh.vehicle_number}",
                    message=f"Vehicle {veh.vehicle_number} requires maintenance (Mileage: {curr_mileage:.1f} km, Next Due: {latest_next:.1f} km).",
                    alert_type=AlertType.MAINTENANCE_DUE.value,
                    severity=AlertSeverity.CRITICAL.value if curr_mileage >= latest_next else AlertSeverity.WARNING.value,
                    created_at=now,
                )
                db_session.add(notif)
                generated.append(self._model_to_dict(notif))

        # 2. URGENT ORDER NOT ASSIGNED
        res_ord = await db_session.execute(
            select(Order).where(
                and_(
                    Order.priority.in_([OrderPriority.URGENT.value, OrderPriority.HIGH.value]),
                    Order.status == OrderStatus.PENDING.value,
                    Order.assigned_driver_id.is_(None),
                )
            )
        )
        urgent_orders = res_ord.scalars().all()
        for ord_item in urgent_orders:
            notif = Notification(
                recipient_role="LOGISTICS_MANAGER",
                order_id=ord_item.id,
                title=f"Urgent Order Unassigned: {ord_item.order_number}",
                message=f"Urgent order {ord_item.order_number} is pending assignment without a driver.",
                alert_type=AlertType.URGENT_ORDER_UNASSIGNED.value,
                severity=AlertSeverity.CRITICAL.value if ord_item.priority == OrderPriority.URGENT.value else AlertSeverity.WARNING.value,
                created_at=now,
            )
            db_session.add(notif)
            generated.append(self._model_to_dict(notif))

        # 3. ROUTE EXCEEDS MAXIMUM DISTANCE
        res_r = await db_session.execute(select(Route).where(Route.total_distance > MAX_ROUTE_DISTANCE_THRESHOLD_KM))
        long_routes = res_r.scalars().all()
        for rt in long_routes:
            notif = Notification(
                recipient_role="LOGISTICS_MANAGER",
                driver_id=rt.driver_id,
                vehicle_id=rt.vehicle_id,
                route_id=rt.id,
                title=f"Route Distance Exceeded: {rt.name}",
                message=f"Route {rt.name} distance ({rt.total_distance:.1f} km) exceeds maximum limit.",
                alert_type=AlertType.ROUTE_EXCEEDS_MAX_DISTANCE.value,
                severity=AlertSeverity.WARNING.value,
                created_at=now,
            )
            db_session.add(notif)
            generated.append(self._model_to_dict(notif))

        # 4. DELIVERY DELAYED
        res_del = await db_session.execute(
            select(Order).where(
                and_(
                    Order.status.in_([OrderStatus.ASSIGNED.value, OrderStatus.OUT_FOR_DELIVERY.value]),
                    Order.delivery_window_end.isnot(None),
                    Order.delivery_window_end < now,
                )
            )
        )
        delayed_orders = res_del.scalars().all()
        for d_ord in delayed_orders:
            notif = Notification(
                recipient_role="LOGISTICS_MANAGER",
                driver_id=d_ord.assigned_driver_id,
                order_id=d_ord.id,
                title=f"Delivery Delayed: Order {d_ord.order_number}",
                message=f"Order {d_ord.order_number} is past scheduled delivery window.",
                alert_type=AlertType.DELIVERY_DELAYED.value,
                severity=AlertSeverity.WARNING.value,
                created_at=now,
            )
            db_session.add(notif)
            generated.append(self._model_to_dict(notif))

        # 5. DRIVER UNAVAILABLE
        res_drv = await db_session.execute(
            select(Driver).where(Driver.status.in_([DriverStatus.OFF_DUTY.value, DriverStatus.INACTIVE.value]))
        )
        unavailable_drivers = res_drv.scalars().all()
        for u_drv in unavailable_drivers:
            # check active orders
            res_d_ord = await db_session.execute(
                select(Order).where(
                    and_(
                        Order.assigned_driver_id == u_drv.id,
                        Order.status.in_([OrderStatus.ASSIGNED.value, OrderStatus.OUT_FOR_DELIVERY.value]),
                    )
                )
            )
            if res_d_ord.scalars().first():
                notif = Notification(
                    recipient_role="LOGISTICS_MANAGER",
                    driver_id=u_drv.id,
                    title=f"Driver Unavailable: Driver {u_drv.license_number}",
                    message=f"Driver {u_drv.license_number} is {u_drv.status} but has active orders assigned.",
                    alert_type=AlertType.DRIVER_UNAVAILABLE.value,
                    severity=AlertSeverity.WARNING.value,
                    created_at=now,
                )
                db_session.add(notif)
                generated.append(self._model_to_dict(notif))

        # 6. VEHICLE OVERLOADED
        for veh in vehicles:
            if veh.driver_id:
                res_w = await db_session.execute(
                    select(Order).where(
                        and_(
                            Order.assigned_driver_id == veh.driver_id,
                            Order.status.in_([OrderStatus.ASSIGNED.value, OrderStatus.OUT_FOR_DELIVERY.value]),
                        )
                    )
                )
                orders_for_veh = res_w.scalars().all()
                total_pkg_weight = sum(o.package_weight for o in orders_for_veh)
                if total_pkg_weight > veh.capacity:
                    notif = Notification(
                        recipient_role="LOGISTICS_MANAGER",
                        driver_id=veh.driver_id,
                        vehicle_id=veh.id,
                        title=f"Vehicle Overloaded: {veh.vehicle_number}",
                        message=f"Vehicle {veh.vehicle_number} total load ({total_pkg_weight:.1f} kg) exceeds capacity ({veh.capacity:.1f} kg).",
                        alert_type=AlertType.VEHICLE_OVERLOADED.value,
                        severity=AlertSeverity.CRITICAL.value,
                        created_at=now,
                    )
                    db_session.add(notif)
                    generated.append(self._model_to_dict(notif))

        await db_session.commit()
        return generated

    def _model_to_dict(self, notif: Notification) -> dict:
        return {
            "id": notif.id,
            "recipient_user_id": notif.recipient_user_id,
            "recipient_role": notif.recipient_role,
            "driver_id": notif.driver_id,
            "vehicle_id": notif.vehicle_id,
            "route_id": notif.route_id,
            "order_id": notif.order_id,
            "title": notif.title,
            "message": notif.message,
            "alert_type": notif.alert_type,
            "severity": notif.severity,
            "is_read": notif.is_read,
            "read_at": notif.read_at,
            "created_at": notif.created_at,
        }

    async def _broadcast_alert(self, alert: dict):
        """Dispatches notification to Redis channel and connected WebSocket clients."""
        payload = {
            "type": "notification_alert",
            "alert": {
                **alert,
                "created_at": alert["created_at"].isoformat() if isinstance(alert["created_at"], datetime) else str(alert["created_at"]),
                "read_at": alert["read_at"].isoformat() if alert.get("read_at") and isinstance(alert["read_at"], datetime) else None,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Publish to redis
        await publish_tracking_event(payload)

        # Broadcast via WebSocket manager
        try:
            from app.api.websockets.tracking import tracking_manager
            # Broadcast to managers
            await tracking_manager.broadcast_to_managers(payload)
            # If targeted to a specific driver, send to driver directly
            if alert.get("driver_id"):
                await tracking_manager.send_to_driver(alert["driver_id"], payload)
        except Exception as ws_err:
            logger.debug(f"WebSocket broadcast error for alert: {ws_err}")


alert_engine = IntelligentAlertEngine()
