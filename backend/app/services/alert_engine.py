import logging
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.redis import publish_tracking_event
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver, DriverStatus
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.route import Route
from app.models.maintenance import MaintenanceStatus
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
        try:
            if db_session:
                db_alerts = await self._evaluate_db_rules(db_session)
                alerts.extend(db_alerts)
            else:
                async with AsyncSessionLocal() as session:
                    db_alerts = await self._evaluate_db_rules(session)
                    alerts.extend(db_alerts)
        except Exception as e:
            logger.error(f"Error evaluating alerts in DB: {e}")

        # Broadcast each alert via WebSocket and Redis
        for alert in alerts:
            await self._broadcast_alert(alert)

        return alerts

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
                    id=str(uuid.uuid4()),
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
                id=str(uuid.uuid4()),
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
                id=str(uuid.uuid4()),
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
                id=str(uuid.uuid4()),
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
                    id=str(uuid.uuid4()),
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
                        id=str(uuid.uuid4()),
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
