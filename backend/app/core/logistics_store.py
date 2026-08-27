import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Initial seeded data for realistic multi-role logistics operations
SEED_WAREHOUSES: Dict[str, dict] = {
    "wh-001": {
        "id": "wh-001",
        "name": "Manhattan Central Logistics Hub",
        "address": "500 W 33rd St, New York, NY",
        "latitude": 40.7538,
        "longitude": -74.0017,
        "capacity": 25000.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "wh-002": {
        "id": "wh-002",
        "name": "Brooklyn Waterfront Distribution",
        "address": "25 53rd St, Brooklyn, NY",
        "latitude": 40.6508,
        "longitude": -74.0152,
        "capacity": 18000.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "wh-003": {
        "id": "wh-003",
        "name": "Queens Cargo Terminal",
        "address": "28-01 Queens Plaza N, Long Island City, NY",
        "latitude": 40.7505,
        "longitude": -73.9372,
        "capacity": 30000.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
}

SEED_CUSTOMERS: Dict[str, dict] = {
    "cust-001": {
        "id": "cust-001",
        "name": "Tech Hub Broadway",
        "phone": "+1-212-555-0144",
        "email": "logistics@techhub.com",
        "address": "450 Broadway, New York, NY",
        "latitude": 40.7209,
        "longitude": -74.0005,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "cust-002": {
        "id": "cust-002",
        "name": "Midtown Health Clinic",
        "phone": "+1-212-555-0182",
        "email": "supplies@midtownhealth.org",
        "address": "200 E 42nd St, New York, NY",
        "latitude": 40.7505,
        "longitude": -73.9735,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "cust-003": {
        "id": "cust-003",
        "name": "Chelsea Market Retail",
        "phone": "+1-212-555-0199",
        "email": "inventory@chelseamarket.com",
        "address": "75 9th Ave, New York, NY",
        "latitude": 40.7420,
        "longitude": -74.0048,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
}

SEED_DRIVERS: Dict[str, dict] = {
    "drv-001": {
        "id": "drv-001",
        "user_id": "usr-drv-003",  # Maps to driver@example.com
        "license_number": "DL-NY-893012",
        "phone": "+1-917-555-0120",
        "status": "ASSIGNED",
        "current_latitude": 40.7128,
        "current_longitude": -74.0060,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "drv-002": {
        "id": "drv-002",
        "user_id": None,
        "license_number": "DL-NY-772910",
        "phone": "+1-917-555-0184",
        "status": "AVAILABLE",
        "current_latitude": 40.6782,
        "current_longitude": -73.9442,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
}

SEED_VEHICLES: Dict[str, dict] = {
    "veh-101": {
        "id": "veh-101",
        "driver_id": "drv-001",
        "vehicle_number": "NY-492-X",
        "vehicle_type": "VAN",
        "capacity": 1200.0,
        "fuel_type": "DIESEL",
        "mileage": 18450.0,
        "status": "IN_TRANSIT",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "veh-102": {
        "id": "veh-102",
        "driver_id": "drv-002",
        "vehicle_number": "NY-781-B",
        "vehicle_type": "VAN",
        "capacity": 1500.0,
        "fuel_type": "ELECTRIC",
        "mileage": 8200.0,
        "status": "AVAILABLE",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "veh-103": {
        "id": "veh-103",
        "driver_id": None,
        "vehicle_number": "NY-994-E",
        "vehicle_type": "TRUCK",
        "capacity": 2500.0,
        "fuel_type": "DIESEL",
        "mileage": 34100.0,
        "status": "AVAILABLE",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
}

SEED_ORDERS: Dict[str, dict] = {
    "ord-001": {
        "id": "ord-001",
        "order_number": "ORD-7001",
        "customer_id": "cust-001",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": 25.0,
        "priority": "HIGH",
        "delivery_window_start": datetime.utcnow(),
        "delivery_window_end": datetime.utcnow() + timedelta(hours=3),
        "status": "ASSIGNED",
        "assigned_driver_id": "drv-001",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "ord-002": {
        "id": "ord-002",
        "order_number": "ORD-7002",
        "customer_id": "cust-002",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7505,
        "delivery_longitude": -73.9735,
        "package_weight": 40.0,
        "priority": "URGENT",
        "delivery_window_start": datetime.utcnow(),
        "delivery_window_end": datetime.utcnow() + timedelta(hours=2),
        "status": "OUT_FOR_DELIVERY",
        "assigned_driver_id": "drv-001",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "ord-003": {
        "id": "ord-003",
        "order_number": "ORD-7003",
        "customer_id": "cust-003",
        "warehouse_id": "wh-002",
        "pickup_latitude": 40.6508,
        "pickup_longitude": -74.0152,
        "delivery_latitude": 40.7420,
        "delivery_longitude": -74.0048,
        "package_weight": 15.0,
        "priority": "NORMAL",
        "delivery_window_start": datetime.utcnow(),
        "delivery_window_end": datetime.utcnow() + timedelta(hours=5),
        "status": "PENDING",
        "assigned_driver_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
}

SEED_OPTIMIZATION_JOBS: Dict[str, dict] = {}
SEED_ROUTES: Dict[str, dict] = {
    "rt-001": {
        "id": "rt-001",
        "name": "Manhattan Morning Delivery Loop",
        "driver_id": "drv-001",
        "vehicle_id": "veh-101",
        "warehouse_id": "wh-001",
        "total_distance": 14.8,
        "estimated_duration": 35.0,
        "optimization_score": 100.0,
        "status": "PLANNED",
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
    }
}

SEED_ROUTE_STOPS: Dict[str, dict] = {
    "stp-001": {
        "id": "stp-001",
        "route_id": "rt-001",
        "order_id": "ord-001",
        "sequence": 1,
        "estimated_arrival": datetime.utcnow() + timedelta(minutes=15),
        "actual_arrival": None,
        "status": "PENDING",
    },
    "stp-002": {
        "id": "stp-002",
        "route_id": "rt-001",
        "order_id": "ord-002",
        "sequence": 2,
        "estimated_arrival": datetime.utcnow() + timedelta(minutes=30),
        "actual_arrival": None,
        "status": "PENDING",
    },
}

SEED_DELIVERY_EVENTS: List[dict] = []
SEED_DRIVER_LOCATIONS: List[dict] = []

SEED_VEHICLE_MAINTENANCE: Dict[str, dict] = {
    "maint-001": {
        "id": "maint-001",
        "vehicle_id": "veh-101",
        "maintenance_type": "OIL_CHANGE",
        "maintenance_date": datetime.utcnow() - timedelta(days=45),
        "mileage": 15000.0,
        "notes": "Full synthetic engine oil replacement and oil filter renewed.",
        "next_maintenance_mileage": 20000.0,
        "cost": 180.0,
        "status": "COMPLETED",
        "created_at": datetime.utcnow() - timedelta(days=45),
        "updated_at": datetime.utcnow() - timedelta(days=45),
    },
    "maint-002": {
        "id": "maint-002",
        "vehicle_id": "veh-102",
        "maintenance_type": "BATTERY_CHECK",
        "maintenance_date": datetime.utcnow() - timedelta(days=20),
        "mileage": 5000.0,
        "notes": "High voltage battery diagnostics and firmware check. Battery health 98%.",
        "next_maintenance_mileage": 10000.0,
        "cost": 120.0,
        "status": "COMPLETED",
        "created_at": datetime.utcnow() - timedelta(days=20),
        "updated_at": datetime.utcnow() - timedelta(days=20),
    },
    "maint-003": {
        "id": "maint-003",
        "vehicle_id": "veh-103",
        "maintenance_type": "BRAKE_INSPECTION",
        "maintenance_date": datetime.utcnow() - timedelta(days=90),
        "mileage": 25000.0,
        "notes": "Brake pads and rotors inspected, brake fluid flushed.",
        "next_maintenance_mileage": 30000.0,  # Note: veh-103 is at 34,100 km, so overdue!
        "cost": 340.0,
        "status": "COMPLETED",
        "created_at": datetime.utcnow() - timedelta(days=90),
        "updated_at": datetime.utcnow() - timedelta(days=90),
    },
}

SEED_NOTIFICATIONS: Dict[str, dict] = {
    "notif-001": {
        "id": "notif-001",
        "recipient_user_id": None,
        "recipient_role": "ADMIN",
        "driver_id": None,
        "vehicle_id": "veh-103",
        "route_id": None,
        "order_id": None,
        "title": "Maintenance Overdue: Vehicle NY-994-E",
        "message": "Vehicle NY-994-E has exceeded scheduled maintenance mileage (Current: 34,100 km, Due: 30,000 km).",
        "alert_type": "MAINTENANCE_DUE",
        "severity": "CRITICAL",
        "is_read": False,
        "read_at": None,
        "created_at": datetime.utcnow() - timedelta(hours=2),
    },
    "notif-002": {
        "id": "notif-002",
        "recipient_user_id": None,
        "recipient_role": "LOGISTICS_MANAGER",
        "driver_id": "drv-001",
        "vehicle_id": "veh-101",
        "route_id": "rt-001",
        "order_id": "ord-002",
        "title": "Urgent Order Assigned",
        "message": "Urgent order ORD-7002 is assigned to driver John Doe on route Manhattan Morning Delivery Loop.",
        "alert_type": "SYSTEM_ALERT",
        "severity": "INFO",
        "is_read": False,
        "read_at": None,
        "created_at": datetime.utcnow() - timedelta(hours=1),
    },
}


def record_driver_location_in_store(
    driver_id: str,
    latitude: float,
    longitude: float,
    accuracy: Optional[float] = None,
    speed: Optional[float] = None,
    heading: Optional[float] = None,
    timestamp: Optional[datetime] = None,
) -> dict:
    """Records a driver GPS location update in the in-memory fallback store."""
    ts = timestamp or datetime.utcnow()
    loc_entry = {
        "id": f"loc-{uuid.uuid4().hex[:8]}",
        "driver_id": driver_id,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "speed": speed,
        "heading": heading,
        "timestamp": ts,
    }
    SEED_DRIVER_LOCATIONS.append(loc_entry)

    # Also update driver's current position and timestamp in SEED_DRIVERS
    if driver_id in SEED_DRIVERS:
        SEED_DRIVERS[driver_id]["current_latitude"] = latitude
        SEED_DRIVERS[driver_id]["current_longitude"] = longitude
        SEED_DRIVERS[driver_id]["speed"] = speed
        SEED_DRIVERS[driver_id]["heading"] = heading
        SEED_DRIVERS[driver_id]["updated_at"] = ts

    return loc_entry


def get_driver_locations_from_store(
    driver_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
) -> List[dict]:
    """Retrieves filtered location history for a driver from the in-memory store."""
    filtered = []
    for loc in SEED_DRIVER_LOCATIONS:
        if loc["driver_id"] != driver_id:
            continue
        ts = loc["timestamp"]
        if start_time and ts < start_time:
            continue
        if end_time and ts > end_time:
            continue
        filtered.append(loc)

    # Sort newest first or chronological based on timestamp
    filtered.sort(key=lambda x: x["timestamp"], reverse=True)
    return filtered[:limit]


# ==============================================================================
# PHASE 12: AUDIT LOGS IN-MEMORY SEED STORE
# ==============================================================================
SEED_AUDIT_LOGS: Dict[str, dict] = {
    "audit-001": {
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
    "audit-002": {
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
    "audit-003": {
        "id": "audit-003",
        "user_id": "usr-mgr-001",
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
    "audit-004": {
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
    "audit-005": {
        "id": "audit-005",
        "user_id": "usr-drv-001",
        "user_email": "driver1@example.com",
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
}

