from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.schemas.map_view import (
    MapOverviewResponse,
    MapDriverItem,
    MapWarehouseItem,
    MapOrderItem,
)
from app.core.logistics_store import (
    SEED_DRIVERS,
    SEED_VEHICLES,
    SEED_WAREHOUSES,
    SEED_CUSTOMERS,
    SEED_ORDERS,
)
from app.core.seed import SEED_USERS

router = APIRouter()


@router.get("/overview", response_model=MapOverviewResponse)
async def get_map_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return geographic data required for the logistics map.
    Enforces RBAC: Admins & Managers see all entities, Drivers see only permitted scopes.
    """
    driver_list: List[MapDriverItem] = []
    warehouse_list: List[MapWarehouseItem] = []
    order_list: List[MapOrderItem] = []

    is_driver = current_user.role == UserRole.DRIVER.value
    driver_profile_id = None

    if is_driver:
        for did, d in SEED_DRIVERS.items():
            if d.get("user_id") == current_user.id:
                driver_profile_id = did
                break

    # 1. Warehouses (Accessible to all authenticated roles)
    for wid, w in SEED_WAREHOUSES.items():
        lat = float(w.get("latitude", 0.0))
        lng = float(w.get("longitude", 0.0))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            warehouse_list.append(
                MapWarehouseItem(
                    id=wid,
                    name=w["name"],
                    address=w["address"],
                    latitude=lat,
                    longitude=lng,
                    capacity=float(w.get("capacity", 10000.0)),
                )
            )

    # 2. Drivers
    for did, d in SEED_DRIVERS.items():
        # If user is a driver, only include their own driver marker
        if is_driver and did != driver_profile_id:
            continue

        lat = d.get("current_latitude")
        lng = d.get("current_longitude")
        if lat is None or lng is None:
            continue

        lat_f = float(lat)
        lng_f = float(lng)
        if not (-90 <= lat_f <= 90 and -180 <= lng_f <= 180):
            continue

        # Resolve driver name
        d_name = f"Driver {d['license_number']}"
        if d.get("user_id"):
            for u in SEED_USERS.values():
                if u["id"] == d["user_id"]:
                    d_name = u["name"]
                    break

        # Resolve vehicle
        v_num = None
        v_type = None
        for v in SEED_VEHICLES.values():
            if v.get("driver_id") == did:
                v_num = v.get("vehicle_number")
                v_type = v.get("vehicle_type")
                break

        driver_list.append(
            MapDriverItem(
                id=did,
                name=d_name,
                license_number=d["license_number"],
                phone=d["phone"],
                status=d["status"],
                latitude=lat_f,
                longitude=lng_f,
                vehicle_number=v_num,
                vehicle_type=v_type,
            )
        )

    # 3. Orders
    for oid, o in SEED_ORDERS.items():
        # If user is a driver, only show orders assigned to them
        if is_driver and o.get("assigned_driver_id") != driver_profile_id:
            continue

        p_lat = float(o.get("pickup_latitude", 0.0))
        p_lng = float(o.get("pickup_longitude", 0.0))
        d_lat = float(o.get("delivery_latitude", 0.0))
        d_lng = float(o.get("delivery_longitude", 0.0))

        if not (-90 <= p_lat <= 90 and -180 <= p_lng <= 180):
            continue
        if not (-90 <= d_lat <= 90 and -180 <= d_lng <= 180):
            continue

        # Resolve customer name & address
        c_name = "Client"
        c_addr = None
        if o.get("customer_id") in SEED_CUSTOMERS:
            cust = SEED_CUSTOMERS[o["customer_id"]]
            c_name = cust.get("name", "Client")
            c_addr = cust.get("address")

        # Resolve driver name
        d_name = None
        if o.get("assigned_driver_id") and o["assigned_driver_id"] in SEED_DRIVERS:
            drv = SEED_DRIVERS[o["assigned_driver_id"]]
            d_name = f"Driver {drv['license_number']}"

        order_list.append(
            MapOrderItem(
                id=oid,
                order_number=o["order_number"],
                customer_name=c_name,
                delivery_address=c_addr,
                pickup_latitude=p_lat,
                pickup_longitude=p_lng,
                delivery_latitude=d_lat,
                delivery_longitude=d_lng,
                priority=o["priority"],
                status=o["status"],
                package_weight=float(o.get("package_weight", 0.0)),
                assigned_driver_id=o.get("assigned_driver_id"),
                assigned_driver_name=d_name,
            )
        )

    return MapOverviewResponse(
        drivers=driver_list,
        warehouses=warehouse_list,
        orders=order_list,
    )
