import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.warehouse import Warehouse
from app.models.customer import Customer
from app.models.driver import Driver, DriverStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.route import Route, RouteStop, RouteStatus, RouteStopStatus
from app.models.maintenance import VehicleMaintenance, MaintenanceType, MaintenanceStatus
from app.models.notification import Notification, AlertType, AlertSeverity
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Pre-computed bcrypt hashes for demo passwords:
# admin@example.com -> Admin@123456
# manager@example.com -> Manager@123456
# driver@example.com -> Driver@123456
ADMIN_PASSWORD_HASH = get_password_hash("Admin@123456")
MANAGER_PASSWORD_HASH = get_password_hash("Manager@123456")
DRIVER_PASSWORD_HASH = get_password_hash("Driver@123456")

SEED_USERS_DATA: List[dict] = [
    {
        "id": "usr-admin-001",
        "name": "System Administrator",
        "email": "admin@example.com",
        "password_hash": ADMIN_PASSWORD_HASH,
        "role": UserRole.ADMIN.value,
        "is_active": True,
    },
    {
        "id": "usr-mgr-002",
        "name": "Logistics Dispatch Manager",
        "email": "manager@example.com",
        "password_hash": MANAGER_PASSWORD_HASH,
        "role": UserRole.LOGISTICS_MANAGER.value,
        "is_active": True,
    },
    {
        "id": "usr-drv-003",
        "name": "David Driver (NYC)",
        "email": "driver@example.com",
        "password_hash": DRIVER_PASSWORD_HASH,
        "role": UserRole.DRIVER.value,
        "is_active": True,
    },
]

# Backward-compatibility dictionary during migration
SEED_USERS: Dict[str, dict] = {
    u["email"]: {**u, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
    for u in SEED_USERS_DATA
}

SEED_WAREHOUSES_DATA: List[dict] = [
    {
        "id": "wh-001",
        "name": "Manhattan Central Logistics Hub",
        "address": "500 W 33rd St, New York, NY",
        "latitude": 40.7538,
        "longitude": -74.0017,
        "capacity": 25000.0,
    },
    {
        "id": "wh-002",
        "name": "Brooklyn Waterfront Distribution",
        "address": "25 53rd St, Brooklyn, NY",
        "latitude": 40.6508,
        "longitude": -74.0152,
        "capacity": 18000.0,
    },
    {
        "id": "wh-003",
        "name": "Queens Cargo Terminal",
        "address": "28-01 Queens Plaza N, Long Island City, NY",
        "latitude": 40.7505,
        "longitude": -73.9372,
        "capacity": 30000.0,
    },
]

SEED_CUSTOMERS_DATA: List[dict] = [
    {
        "id": "cust-001",
        "name": "Tech Hub Broadway",
        "phone": "+1-212-555-0144",
        "email": "logistics@techhub.com",
        "address": "450 Broadway, New York, NY",
        "latitude": 40.7209,
        "longitude": -74.0005,
    },
    {
        "id": "cust-002",
        "name": "Midtown Health Clinic",
        "phone": "+1-212-555-0182",
        "email": "supplies@midtownhealth.org",
        "address": "200 E 42nd St, New York, NY",
        "latitude": 40.7505,
        "longitude": -73.9735,
    },
    {
        "id": "cust-003",
        "name": "Chelsea Market Retail",
        "phone": "+1-212-555-0199",
        "email": "inventory@chelseamarket.com",
        "address": "75 9th Ave, New York, NY",
        "latitude": 40.7420,
        "longitude": -74.0048,
    },
]

SEED_DRIVERS_DATA: List[dict] = [
    {
        "id": "drv-001",
        "user_id": "usr-drv-003",
        "license_number": "DL-NY-893012",
        "phone": "+1-917-555-0120",
        "status": DriverStatus.ASSIGNED.value,
        "current_latitude": 40.7128,
        "current_longitude": -74.0060,
    },
    {
        "id": "drv-002",
        "user_id": None,
        "license_number": "DL-NY-772910",
        "phone": "+1-917-555-0184",
        "status": DriverStatus.AVAILABLE.value,
        "current_latitude": 40.6782,
        "current_longitude": -73.9442,
    },
]

SEED_VEHICLES_DATA: List[dict] = [
    {
        "id": "veh-101",
        "driver_id": "drv-001",
        "vehicle_number": "NY-492-X",
        "vehicle_type": "VAN",
        "capacity": 1200.0,
        "fuel_type": "DIESEL",
        "mileage": 18450.0,
        "status": VehicleStatus.IN_TRANSIT.value,
    },
    {
        "id": "veh-102",
        "driver_id": "drv-002",
        "vehicle_number": "NY-781-B",
        "vehicle_type": "VAN",
        "capacity": 1500.0,
        "fuel_type": "ELECTRIC",
        "mileage": 8200.0,
        "status": VehicleStatus.AVAILABLE.value,
    },
    {
        "id": "veh-103",
        "driver_id": None,
        "vehicle_number": "NY-994-E",
        "vehicle_type": "TRUCK",
        "capacity": 2500.0,
        "fuel_type": "DIESEL",
        "mileage": 34100.0,
        "status": VehicleStatus.AVAILABLE.value,
    },
]

SEED_ORDERS_DATA: List[dict] = [
    {
        "id": "ord-001",
        "order_number": "ORD-7001",
        "customer_id": "cust-001",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": 25.0,
        "priority": OrderPriority.HIGH.value,
        "delivery_window_start": datetime.utcnow(),
        "delivery_window_end": datetime.utcnow() + timedelta(hours=3),
        "status": OrderStatus.ASSIGNED.value,
        "assigned_driver_id": "drv-001",
    },
    {
        "id": "ord-002",
        "order_number": "ORD-7002",
        "customer_id": "cust-002",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7505,
        "delivery_longitude": -73.9735,
        "package_weight": 40.0,
        "priority": OrderPriority.URGENT.value,
        "delivery_window_start": datetime.utcnow(),
        "delivery_window_end": datetime.utcnow() + timedelta(hours=2),
        "status": OrderStatus.OUT_FOR_DELIVERY.value,
        "assigned_driver_id": "drv-001",
    },
    {
        "id": "ord-003",
        "order_number": "ORD-7003",
        "customer_id": "cust-003",
        "warehouse_id": "wh-002",
        "pickup_latitude": 40.6508,
        "pickup_longitude": -74.0152,
        "delivery_latitude": 40.7420,
        "delivery_longitude": -74.0048,
        "package_weight": 15.0,
        "priority": OrderPriority.NORMAL.value,
        "delivery_window_start": datetime.utcnow(),
        "delivery_window_end": datetime.utcnow() + timedelta(hours=5),
        "status": OrderStatus.PENDING.value,
        "assigned_driver_id": None,
    },
]

SEED_ROUTES_DATA: List[dict] = [
    {
        "id": "rt-001",
        "name": "Manhattan Morning Delivery Loop",
        "driver_id": "drv-001",
        "vehicle_id": "veh-101",
        "warehouse_id": "wh-001",
        "total_distance": 14.8,
        "estimated_duration": 35.0,
        "optimization_score": 100.0,
        "status": RouteStatus.PLANNED.value,
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
    }
]

SEED_ROUTE_STOPS_DATA: List[dict] = [
    {
        "id": "stp-001",
        "route_id": "rt-001",
        "order_id": "ord-001",
        "sequence": 1,
        "estimated_arrival": datetime.utcnow() + timedelta(minutes=15),
        "actual_arrival": None,
        "status": RouteStopStatus.PENDING.value,
    },
    {
        "id": "stp-002",
        "route_id": "rt-001",
        "order_id": "ord-002",
        "sequence": 2,
        "estimated_arrival": datetime.utcnow() + timedelta(minutes=30),
        "actual_arrival": None,
        "status": RouteStopStatus.PENDING.value,
    },
]

SEED_MAINTENANCE_DATA: List[dict] = [
    {
        "id": "maint-001",
        "vehicle_id": "veh-101",
        "maintenance_type": MaintenanceType.OIL_CHANGE.value,
        "maintenance_date": datetime.utcnow() - timedelta(days=45),
        "mileage": 15000.0,
        "notes": "Full synthetic engine oil replacement and oil filter renewed.",
        "next_maintenance_mileage": 20000.0,
        "cost": 180.0,
        "status": MaintenanceStatus.COMPLETED.value,
    },
    {
        "id": "maint-002",
        "vehicle_id": "veh-102",
        "maintenance_type": MaintenanceType.BATTERY_CHECK.value,
        "maintenance_date": datetime.utcnow() - timedelta(days=20),
        "mileage": 5000.0,
        "notes": "High voltage battery diagnostics and firmware check. Battery health 98%.",
        "next_maintenance_mileage": 10000.0,
        "cost": 120.0,
        "status": MaintenanceStatus.COMPLETED.value,
    },
    {
        "id": "maint-003",
        "vehicle_id": "veh-103",
        "maintenance_type": MaintenanceType.BRAKE_INSPECTION.value,
        "maintenance_date": datetime.utcnow() - timedelta(days=90),
        "mileage": 25000.0,
        "notes": "Brake pads and rotors inspected, brake fluid flushed.",
        "next_maintenance_mileage": 30000.0,
        "cost": 340.0,
        "status": MaintenanceStatus.COMPLETED.value,
    },
]

SEED_NOTIFICATIONS_DATA: List[dict] = [
    {
        "id": "notif-001",
        "recipient_user_id": None,
        "recipient_role": "ADMIN",
        "driver_id": None,
        "vehicle_id": "veh-103",
        "route_id": None,
        "order_id": None,
        "title": "Maintenance Overdue: Vehicle NY-994-E",
        "message": "Vehicle NY-994-E has exceeded scheduled maintenance mileage (Current: 34,100 km, Due: 30,000 km).",
        "alert_type": AlertType.MAINTENANCE_DUE.value,
        "severity": AlertSeverity.CRITICAL.value,
        "is_read": False,
        "read_at": None,
        "created_at": datetime.utcnow() - timedelta(hours=2),
    },
    {
        "id": "notif-002",
        "recipient_user_id": None,
        "recipient_role": "LOGISTICS_MANAGER",
        "driver_id": "drv-001",
        "vehicle_id": "veh-101",
        "route_id": "rt-001",
        "order_id": "ord-002",
        "title": "Urgent Order Assigned",
        "message": "Urgent order ORD-7002 is assigned to driver John Doe on route Manhattan Morning Delivery Loop.",
        "alert_type": AlertType.SYSTEM_ALERT.value,
        "severity": AlertSeverity.INFO.value,
        "is_read": False,
        "read_at": None,
        "created_at": datetime.utcnow() - timedelta(hours=1),
    },
]

SEED_AUDIT_LOGS_DATA: List[dict] = [
    {
        "id": "audit-001",
        "user_id": "usr-admin-001",
        "user_email": "admin@example.com",
        "user_role": "ADMIN",
        "action": "SYSTEM_INITIALIZATION",
        "resource_type": "SYSTEM",
        "resource_id": "core-v1",
        "ip_address": "127.0.0.1",
        "user_agent": "SmartLogisticsSystem/1.0",
        "timestamp": datetime.utcnow() - timedelta(hours=24),
        "success": True,
        "details": '{"message": "Fleet database initialized with security hardening and encryption"}',
    },
    {
        "id": "audit-002",
        "user_id": "usr-admin-001",
        "user_email": "admin@example.com",
        "user_role": "ADMIN",
        "action": "USER_LOGIN",
        "resource_type": "AUTH",
        "resource_id": "usr-admin-001",
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "timestamp": datetime.utcnow() - timedelta(hours=5),
        "success": True,
        "details": '{"auth_method": "password", "session_type": "jwt_bearer"}',
    },
    {
        "id": "audit-003",
        "user_id": "usr-mgr-002",
        "user_email": "manager@example.com",
        "user_role": "LOGISTICS_MANAGER",
        "action": "ROUTE_OPTIMIZE",
        "resource_type": "ROUTE",
        "resource_id": "job-opt-seed-1",
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "timestamp": datetime.utcnow() - timedelta(hours=3),
        "success": True,
        "details": '{"warehouse_id": "wh-001", "solver": "OR-Tools", "orders_count": 6, "vehicles_count": 2}',
    },
    {
        "id": "audit-004",
        "user_id": None,
        "user_email": "unknown_intruder@test.com",
        "user_role": None,
        "action": "LOGIN_FAILED",
        "resource_type": "AUTH",
        "resource_id": "auth-attempt",
        "ip_address": "203.0.113.195",
        "user_agent": "python-requests/2.31.0",
        "timestamp": datetime.utcnow() - timedelta(hours=2),
        "success": False,
        "details": '{"reason": "Invalid credentials", "attempt_count": 1}',
    },
    {
        "id": "audit-005",
        "user_id": "usr-drv-003",
        "user_email": "driver@example.com",
        "user_role": "DRIVER",
        "action": "ORDER_STATUS_CHANGE",
        "resource_type": "ORDER",
        "resource_id": "ord-001",
        "ip_address": "172.56.21.89",
        "user_agent": "SmartLogisticsMobile/2.4 (Android 14)",
        "timestamp": datetime.utcnow() - timedelta(minutes=45),
        "success": True,
        "details": '{"previous_status": "OUT_FOR_DELIVERY", "new_status": "DELIVERED", "signature_verified": true}',
    },
]


async def seed_demo_data(db: AsyncSession) -> None:
    """
    Idempotently seeds all core operational data into the relational database.
    Safe to execute repeatedly without duplicating records or creating constraint violations.
    """
    logger.info("Checking and seeding demo data into database...")
    now = datetime.utcnow()

    # 1. Users
    for u_data in SEED_USERS_DATA:
        existing = await db.execute(select(User).where(User.id == u_data["id"]))
        if not existing.scalar_one_or_none():
            user = User(
                id=u_data["id"],
                name=u_data["name"],
                email=u_data["email"],
                password_hash=u_data["password_hash"],
                role=u_data["role"],
                is_active=u_data["is_active"],
                created_at=now,
                updated_at=now,
            )
            db.add(user)
    await db.flush()

    # 2. Warehouses
    for wh_data in SEED_WAREHOUSES_DATA:
        existing = await db.execute(select(Warehouse).where(Warehouse.id == wh_data["id"]))
        if not existing.scalar_one_or_none():
            wh = Warehouse(
                id=wh_data["id"],
                name=wh_data["name"],
                address=wh_data["address"],
                latitude=wh_data["latitude"],
                longitude=wh_data["longitude"],
                capacity=wh_data["capacity"],
                created_at=now,
                updated_at=now,
            )
            db.add(wh)
    await db.flush()

    # 3. Customers
    for cust_data in SEED_CUSTOMERS_DATA:
        existing = await db.execute(select(Customer).where(Customer.id == cust_data["id"]))
        if not existing.scalar_one_or_none():
            cust = Customer(
                id=cust_data["id"],
                name=cust_data["name"],
                phone=cust_data["phone"],
                email=cust_data["email"],
                address=cust_data["address"],
                latitude=cust_data["latitude"],
                longitude=cust_data["longitude"],
                created_at=now,
                updated_at=now,
            )
            db.add(cust)
    await db.flush()

    # 4. Drivers
    for drv_data in SEED_DRIVERS_DATA:
        existing = await db.execute(select(Driver).where(Driver.id == drv_data["id"]))
        if not existing.scalar_one_or_none():
            drv = Driver(
                id=drv_data["id"],
                user_id=drv_data["user_id"],
                license_number=drv_data["license_number"],
                phone=drv_data["phone"],
                status=drv_data["status"],
                current_latitude=drv_data["current_latitude"],
                current_longitude=drv_data["current_longitude"],
                created_at=now,
                updated_at=now,
            )
            db.add(drv)
    await db.flush()

    # 5. Vehicles
    for veh_data in SEED_VEHICLES_DATA:
        existing = await db.execute(select(Vehicle).where(Vehicle.id == veh_data["id"]))
        if not existing.scalar_one_or_none():
            veh = Vehicle(
                id=veh_data["id"],
                driver_id=veh_data["driver_id"],
                vehicle_number=veh_data["vehicle_number"],
                vehicle_type=veh_data["vehicle_type"],
                capacity=veh_data["capacity"],
                fuel_type=veh_data["fuel_type"],
                mileage=veh_data["mileage"],
                status=veh_data["status"],
                created_at=now,
                updated_at=now,
            )
            db.add(veh)
    await db.flush()

    # 6. Orders
    for ord_data in SEED_ORDERS_DATA:
        existing = await db.execute(select(Order).where(Order.id == ord_data["id"]))
        if not existing.scalar_one_or_none():
            order = Order(
                id=ord_data["id"],
                order_number=ord_data["order_number"],
                customer_id=ord_data["customer_id"],
                warehouse_id=ord_data["warehouse_id"],
                pickup_latitude=ord_data["pickup_latitude"],
                pickup_longitude=ord_data["pickup_longitude"],
                delivery_latitude=ord_data["delivery_latitude"],
                delivery_longitude=ord_data["delivery_longitude"],
                package_weight=ord_data["package_weight"],
                priority=ord_data["priority"],
                delivery_window_start=ord_data["delivery_window_start"],
                delivery_window_end=ord_data["delivery_window_end"],
                status=ord_data["status"],
                assigned_driver_id=ord_data["assigned_driver_id"],
                created_at=now,
                updated_at=now,
            )
            db.add(order)
    await db.flush()

    # 7. Routes
    for rt_data in SEED_ROUTES_DATA:
        existing = await db.execute(select(Route).where(Route.id == rt_data["id"]))
        if not existing.scalar_one_or_none():
            rt = Route(
                id=rt_data["id"],
                name=rt_data["name"],
                driver_id=rt_data["driver_id"],
                vehicle_id=rt_data["vehicle_id"],
                warehouse_id=rt_data["warehouse_id"],
                total_distance=rt_data["total_distance"],
                estimated_duration=rt_data["estimated_duration"],
                optimization_score=rt_data["optimization_score"],
                status=rt_data["status"],
                created_at=rt_data["created_at"],
                started_at=rt_data["started_at"],
                completed_at=rt_data["completed_at"],
            )
            db.add(rt)
    await db.flush()

    # 8. Route Stops
    for stp_data in SEED_ROUTE_STOPS_DATA:
        existing = await db.execute(select(RouteStop).where(RouteStop.id == stp_data["id"]))
        if not existing.scalar_one_or_none():
            stp = RouteStop(
                id=stp_data["id"],
                route_id=stp_data["route_id"],
                order_id=stp_data["order_id"],
                sequence=stp_data["sequence"],
                estimated_arrival=stp_data["estimated_arrival"],
                actual_arrival=stp_data["actual_arrival"],
                status=stp_data["status"],
                created_at=now,
            )
            db.add(stp)
    await db.flush()

    # 9. Vehicle Maintenance
    for maint_data in SEED_MAINTENANCE_DATA:
        existing = await db.execute(select(VehicleMaintenance).where(VehicleMaintenance.id == maint_data["id"]))
        if not existing.scalar_one_or_none():
            maint = VehicleMaintenance(
                id=maint_data["id"],
                vehicle_id=maint_data["vehicle_id"],
                maintenance_type=maint_data["maintenance_type"],
                maintenance_date=maint_data["maintenance_date"],
                mileage=maint_data["mileage"],
                notes=maint_data["notes"],
                next_maintenance_mileage=maint_data["next_maintenance_mileage"],
                cost=maint_data["cost"],
                status=maint_data["status"],
                created_at=now,
                updated_at=now,
            )
            db.add(maint)
    await db.flush()

    # 10. Notifications
    for notif_data in SEED_NOTIFICATIONS_DATA:
        existing = await db.execute(select(Notification).where(Notification.id == notif_data["id"]))
        if not existing.scalar_one_or_none():
            notif = Notification(
                id=notif_data["id"],
                recipient_user_id=notif_data["recipient_user_id"],
                recipient_role=notif_data["recipient_role"],
                driver_id=notif_data["driver_id"],
                vehicle_id=notif_data["vehicle_id"],
                route_id=notif_data["route_id"],
                order_id=notif_data["order_id"],
                title=notif_data["title"],
                message=notif_data["message"],
                alert_type=notif_data["alert_type"],
                severity=notif_data["severity"],
                is_read=notif_data["is_read"],
                read_at=notif_data["read_at"],
                created_at=notif_data["created_at"],
            )
            db.add(notif)
    await db.flush()

    # 11. Audit Logs
    for audit_data in SEED_AUDIT_LOGS_DATA:
        existing = await db.execute(select(AuditLog).where(AuditLog.id == audit_data["id"]))
        if not existing.scalar_one_or_none():
            log = AuditLog(
                id=audit_data["id"],
                user_id=audit_data["user_id"],
                user_email=audit_data["user_email"],
                user_role=audit_data["user_role"],
                action=audit_data["action"],
                resource_type=audit_data["resource_type"],
                resource_id=audit_data["resource_id"],
                ip_address=audit_data["ip_address"],
                user_agent=audit_data["user_agent"],
                timestamp=audit_data["timestamp"],
                success=audit_data["success"],
                details=audit_data["details"],
            )
            db.add(log)
    await db.flush()

    await db.commit()
    logger.info("Demo data seeding completed successfully.")


async def main():
    from app.core.database import AsyncSessionLocal, engine, Base
    logging.basicConfig(level=logging.INFO)
    print("Connecting to database and ensuring schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_demo_data(session)
    await engine.dispose()
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
