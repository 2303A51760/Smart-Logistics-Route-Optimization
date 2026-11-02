import uuid
import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_db
from app.api.deps import get_current_user, require_manager
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.customer import Customer
from app.models.warehouse import Warehouse
from app.models.driver import Driver
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse
from app.services.audit_service import audit_service

router = APIRouter()


async def _get_driver_id_for_user(user_id: str, db: AsyncSession) -> Optional[str]:
    stmt = select(Driver.id).where(Driver.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


def _format_order_row(o: Order, customer_name: Optional[str], warehouse_name: Optional[str], driver_license: Optional[str]) -> OrderResponse:
    drv_name = f"Driver {driver_license}" if driver_license else None
    return OrderResponse(
        id=o.id,
        order_number=o.order_number,
        customer_id=o.customer_id,
        warehouse_id=o.warehouse_id,
        pickup_latitude=o.pickup_latitude,
        pickup_longitude=o.pickup_longitude,
        delivery_latitude=o.delivery_latitude,
        delivery_longitude=o.delivery_longitude,
        package_weight=o.package_weight,
        priority=OrderPriority(o.priority) if isinstance(o.priority, str) else o.priority,
        delivery_window_start=o.delivery_window_start,
        delivery_window_end=o.delivery_window_end,
        status=OrderStatus(o.status) if isinstance(o.status, str) else o.status,
        assigned_driver_id=o.assigned_driver_id,
        created_at=o.created_at,
        updated_at=o.updated_at,
        customer_name=customer_name or "Unknown Customer",
        warehouse_name=warehouse_name or "Unknown Warehouse",
        assigned_driver_name=drv_name,
    )


@router.get("", response_model=OrderListResponse)
async def list_orders(
    search: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    priority: Optional[OrderPriority] = None,
    driver_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List orders with filtering, search, and pagination. Drivers only see their assigned orders."""
    stmt = (
        select(Order, Customer.name.label("customer_name"), Warehouse.name.label("warehouse_name"), Driver.license_number.label("driver_license"))
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .outerjoin(Warehouse, Order.warehouse_id == Warehouse.id)
        .outerjoin(Driver, Order.assigned_driver_id == Driver.id)
    )

    count_stmt = (
        select(func.count(Order.id))
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .outerjoin(Warehouse, Order.warehouse_id == Warehouse.id)
        .outerjoin(Driver, Order.assigned_driver_id == Driver.id)
    )

    # Role filter: Drivers only see their own assigned deliveries
    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = await _get_driver_id_for_user(current_user.id, db)
        stmt = stmt.where(Order.assigned_driver_id == user_driver_id)
        count_stmt = count_stmt.where(Order.assigned_driver_id == user_driver_id)
    elif driver_id:
        stmt = stmt.where(Order.assigned_driver_id == driver_id)
        count_stmt = count_stmt.where(Order.assigned_driver_id == driver_id)

    if warehouse_id:
        stmt = stmt.where(Order.warehouse_id == warehouse_id)
        count_stmt = count_stmt.where(Order.warehouse_id == warehouse_id)

    if status:
        status_val = status.value if hasattr(status, "value") else str(status)
        stmt = stmt.where(Order.status == status_val)
        count_stmt = count_stmt.where(Order.status == status_val)

    if priority:
        priority_val = priority.value if hasattr(priority, "value") else str(priority)
        stmt = stmt.where(Order.priority == priority_val)
        count_stmt = count_stmt.where(Order.priority == priority_val)

    if search:
        search_filter = or_(
            Order.order_number.ilike(f"%{search}%"),
            Customer.name.ilike(f"%{search}%"),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    total_pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    rows = result.all()

    formatted_items = [
        _format_order_row(order, cust_name, wh_name, drv_lic)
        for order, cust_name, wh_name, drv_lic in rows
    ]

    return {
        "items": formatted_items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
    }


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a new delivery order (Admin/Manager only)."""
    if order_in.package_weight <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Package weight must be greater than 0",
        )

    for lat, lng, label in [
        (order_in.pickup_latitude, order_in.pickup_longitude, "Pickup"),
        (order_in.delivery_latitude, order_in.delivery_longitude, "Delivery"),
    ]:
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{label} coordinates out of valid range",
            )

    cust_res = await db.execute(select(Customer.name).where(Customer.id == order_in.customer_id))
    cust_name = cust_res.scalar_one_or_none()
    if not cust_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer '{order_in.customer_id}' does not exist",
        )

    wh_res = await db.execute(select(Warehouse.name).where(Warehouse.id == order_in.warehouse_id))
    wh_name = wh_res.scalar_one_or_none()
    if not wh_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Warehouse '{order_in.warehouse_id}' does not exist",
        )

    driver_license = None
    if order_in.assigned_driver_id:
        drv_res = await db.execute(select(Driver.license_number).where(Driver.id == order_in.assigned_driver_id))
        driver_license = drv_res.scalar_one_or_none()
        if not driver_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver '{order_in.assigned_driver_id}' does not exist",
            )

    existing_order = await db.execute(select(Order.id).where(Order.order_number == order_in.order_number))
    if existing_order.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order with order number '{order_in.order_number}' already exists",
        )

    new_id = f"ord-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()
    priority_val = order_in.priority.value if hasattr(order_in.priority, "value") else str(order_in.priority)
    status_val = order_in.status.value if hasattr(order_in.status, "value") else str(order_in.status)

    new_order = Order(
        id=new_id,
        order_number=order_in.order_number,
        customer_id=order_in.customer_id,
        warehouse_id=order_in.warehouse_id,
        pickup_latitude=order_in.pickup_latitude,
        pickup_longitude=order_in.pickup_longitude,
        delivery_latitude=order_in.delivery_latitude,
        delivery_longitude=order_in.delivery_longitude,
        package_weight=order_in.package_weight,
        priority=priority_val,
        delivery_window_start=order_in.delivery_window_start or now,
        delivery_window_end=order_in.delivery_window_end or now,
        status=status_val,
        assigned_driver_id=order_in.assigned_driver_id,
        created_at=now,
        updated_at=now,
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    await audit_service.log_event(
        action="ORDER_CREATE",
        user=current_user,
        resource_type="ORDER",
        resource_id=new_id,
        success=True,
        details={
            "order_number": order_in.order_number,
            "customer_id": order_in.customer_id,
            "warehouse_id": order_in.warehouse_id,
            "weight": order_in.package_weight,
            "priority": priority_val,
        },
        db=db,
    )

    return _format_order_row(new_order, cust_name, wh_name, driver_license)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single order details."""
    stmt = (
        select(Order, Customer.name.label("customer_name"), Warehouse.name.label("warehouse_name"), Driver.license_number.label("driver_license"))
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .outerjoin(Warehouse, Order.warehouse_id == Warehouse.id)
        .outerjoin(Driver, Order.assigned_driver_id == Driver.id)
        .where(Order.id == order_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order, cust_name, wh_name, drv_lic = row

    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = await _get_driver_id_for_user(current_user.id, db)
        if order.assigned_driver_id != user_driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this order",
            )

    return _format_order_row(order, cust_name, wh_name, drv_lic)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_in: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update order details or status."""
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.status

    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = await _get_driver_id_for_user(current_user.id, db)
        if order.assigned_driver_id != user_driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update status for orders assigned to you",
            )
        if order_in.status:
            order.status = order_in.status.value if hasattr(order_in.status, "value") else str(order_in.status)
    else:
        if order_in.order_number and order_in.order_number != order.order_number:
            existing = await db.execute(select(Order.id).where(Order.order_number == order_in.order_number, Order.id != order_id))
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order number already exists",
                )
            order.order_number = order_in.order_number

        if order_in.customer_id:
            c_res = await db.execute(select(Customer.id).where(Customer.id == order_in.customer_id))
            if not c_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer does not exist",
                )
            order.customer_id = order_in.customer_id

        if order_in.warehouse_id:
            w_res = await db.execute(select(Warehouse.id).where(Warehouse.id == order_in.warehouse_id))
            if not w_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Warehouse does not exist",
                )
            order.warehouse_id = order_in.warehouse_id

        if order_in.assigned_driver_id is not None:
            if order_in.assigned_driver_id:
                d_res = await db.execute(select(Driver.id).where(Driver.id == order_in.assigned_driver_id))
                if not d_res.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Driver does not exist",
                    )
            order.assigned_driver_id = order_in.assigned_driver_id

        if order_in.package_weight is not None:
            if order_in.package_weight <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Package weight must be greater than 0",
                )
            order.package_weight = order_in.package_weight

        if order_in.pickup_latitude is not None:
            order.pickup_latitude = order_in.pickup_latitude
        if order_in.pickup_longitude is not None:
            order.pickup_longitude = order_in.pickup_longitude
        if order_in.delivery_latitude is not None:
            order.delivery_latitude = order_in.delivery_latitude
        if order_in.delivery_longitude is not None:
            order.delivery_longitude = order_in.delivery_longitude

        if order_in.priority:
            order.priority = order_in.priority.value if hasattr(order_in.priority, "value") else str(order_in.priority)
        if order_in.status:
            order.status = order_in.status.value if hasattr(order_in.status, "value") else str(order_in.status)
        if order_in.delivery_window_start:
            order.delivery_window_start = order_in.delivery_window_start
        if order_in.delivery_window_end:
            order.delivery_window_end = order_in.delivery_window_end

    order.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(order)

    action_name = "ORDER_STATUS_CHANGE" if order_in.status and order.status != old_status else "ORDER_UPDATE"
    await audit_service.log_event(
        action=action_name,
        user=current_user,
        resource_type="ORDER",
        resource_id=order_id,
        success=True,
        details={
            "order_number": order.order_number,
            "old_status": old_status,
            "new_status": order.status,
        },
        db=db,
    )

    cust_res = await db.execute(select(Customer.name).where(Customer.id == order.customer_id))
    cust_name = cust_res.scalar_one_or_none()
    wh_res = await db.execute(select(Warehouse.name).where(Warehouse.id == order.warehouse_id))
    wh_name = wh_res.scalar_one_or_none()
    drv_lic = None
    if order.assigned_driver_id:
        d_res = await db.execute(select(Driver.license_number).where(Driver.id == order.assigned_driver_id))
        drv_lic = d_res.scalar_one_or_none()

    return _format_order_row(order, cust_name, wh_name, drv_lic)


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(
    order_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete order (Admin/Manager only)."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_number = order.order_number
    await db.delete(order)
    await db.commit()

    await audit_service.log_event(
        action="ORDER_DELETE",
        user=current_user,
        resource_type="ORDER",
        resource_id=order_id,
        success=True,
        details={"order_number": order_number},
        db=db,
    )

    return {"status": "success", "message": f"Order {order_id} deleted successfully"}
