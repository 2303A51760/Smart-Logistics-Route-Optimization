from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.warehouse import Warehouse
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.map_view import (
    MapOverviewResponse,
    MapDriverItem,
    MapWarehouseItem,
    MapOrderItem,
)

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
        drv_res = await db.execute(select(Driver.id).where(Driver.user_id == current_user.id))
        driver_profile_id = drv_res.scalar_one_or_none()

    # 1. Warehouses
    wh_res = await db.execute(select(Warehouse).order_by(Warehouse.name))
    for w in wh_res.scalars().all():
        lat = float(w.latitude or 0.0)
        lng = float(w.longitude or 0.0)
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            warehouse_list.append(
                MapWarehouseItem(
                    id=w.id,
                    name=w.name,
                    address=w.address,
                    latitude=lat,
                    longitude=lng,
                    capacity=float(w.capacity or 10000.0),
                )
            )

    # 2. Drivers
    drv_stmt = select(Driver)
    if is_driver:
        if driver_profile_id:
            drv_stmt = drv_stmt.where(Driver.id == driver_profile_id)
        else:
            drv_stmt = drv_stmt.where(Driver.user_id == current_user.id)

    drivers_res = await db.execute(drv_stmt)
    drivers = drivers_res.scalars().all()

    user_ids = [d.user_id for d in drivers if d.user_id]
    users_map = {}
    if user_ids:
        u_res = await db.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
        users_map = dict(u_res.all())

    driver_ids = [d.id for d in drivers]
    vehicles_map = {}
    if driver_ids:
        v_res = await db.execute(select(Vehicle.driver_id, Vehicle.vehicle_number, Vehicle.vehicle_type).where(Vehicle.driver_id.in_(driver_ids)))
        for d_id, v_num, v_type in v_res.all():
            vehicles_map[d_id] = (v_num, v_type)

    for d in drivers:
        lat = d.current_latitude
        lng = d.current_longitude
        if lat is None or lng is None:
            continue

        lat_f = float(lat)
        lng_f = float(lng)
        if not (-90 <= lat_f <= 90 and -180 <= lng_f <= 180):
            continue

        d_name = users_map.get(d.user_id, f"Driver {d.license_number}")
        v_num, v_type = vehicles_map.get(d.id, (None, None))

        driver_list.append(
            MapDriverItem(
                id=d.id,
                name=d_name,
                license_number=d.license_number,
                phone=d.phone,
                status=d.status,
                latitude=lat_f,
                longitude=lng_f,
                vehicle_number=v_num,
                vehicle_type=v_type,
            )
        )

    # 3. Orders
    order_stmt = (
        select(Order, Customer.name.label("customer_name"), Customer.address.label("delivery_address"), Driver.license_number.label("driver_license"))
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .outerjoin(Driver, Order.assigned_driver_id == Driver.id)
    )
    if is_driver:
        order_stmt = order_stmt.where(Order.assigned_driver_id == driver_profile_id)

    orders_res = await db.execute(order_stmt)
    for o, c_name, c_addr, drv_lic in orders_res.all():
        p_lat = float(o.pickup_latitude or 0.0)
        p_lng = float(o.pickup_longitude or 0.0)
        d_lat = float(o.delivery_latitude or 0.0)
        d_lng = float(o.delivery_longitude or 0.0)

        if not (-90 <= p_lat <= 90 and -180 <= p_lng <= 180):
            continue
        if not (-90 <= d_lat <= 90 and -180 <= d_lng <= 180):
            continue

        drv_name = f"Driver {drv_lic}" if drv_lic else None

        order_list.append(
            MapOrderItem(
                id=o.id,
                order_number=o.order_number,
                customer_name=c_name or "Client",
                delivery_address=c_addr,
                pickup_latitude=p_lat,
                pickup_longitude=p_lng,
                delivery_latitude=d_lat,
                delivery_longitude=d_lng,
                priority=o.priority,
                status=o.status,
                package_weight=float(o.package_weight or 0.0),
                assigned_driver_id=o.assigned_driver_id,
                assigned_driver_name=drv_name,
            )
        )

    return MapOverviewResponse(
        drivers=driver_list,
        warehouses=warehouse_list,
        orders=order_list,
    )
