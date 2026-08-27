import uuid
import math
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user, require_manager
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus, OrderPriority
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse
from app.core.logistics_store import SEED_ORDERS, SEED_CUSTOMERS, SEED_WAREHOUSES, SEED_DRIVERS
from app.services.audit_service import audit_service

router = APIRouter()


def _format_order(o: dict) -> dict:
    cust = SEED_CUSTOMERS.get(o.get("customer_id"))
    cust_name = cust["name"] if cust else "Unknown Customer"

    wh = SEED_WAREHOUSES.get(o.get("warehouse_id"))
    wh_name = wh["name"] if wh else "Unknown Warehouse"

    drv = SEED_DRIVERS.get(o.get("assigned_driver_id"))
    drv_name = f"Driver {drv['license_number']}" if drv else None

    return {
        **o,
        "customer_name": cust_name,
        "warehouse_name": wh_name,
        "assigned_driver_name": drv_name,
    }


def _get_driver_id_for_user(user_id: str) -> Optional[str]:
    for did, d in SEED_DRIVERS.items():
        if d.get("user_id") == user_id:
            return did
    return None


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
    all_orders = list(SEED_ORDERS.values())

    # Role filter: Drivers only see their own assigned deliveries
    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = _get_driver_id_for_user(current_user.id)
        all_orders = [o for o in all_orders if o.get("assigned_driver_id") == user_driver_id]
    elif driver_id:
        all_orders = [o for o in all_orders if o.get("assigned_driver_id") == driver_id]

    if warehouse_id:
        all_orders = [o for o in all_orders if o.get("warehouse_id") == warehouse_id]

    if status:
        all_orders = [o for o in all_orders if o.get("status") == status.value]

    if priority:
        all_orders = [o for o in all_orders if o.get("priority") == priority.value]

    if search:
        s = search.lower()
        filtered = []
        for o in all_orders:
            cust = SEED_CUSTOMERS.get(o.get("customer_id"), {})
            cust_name = cust.get("name", "").lower()
            order_num = o.get("order_number", "").lower()
            if s in order_num or s in cust_name:
                filtered.append(o)
        all_orders = filtered

    # Sort descending by created_at
    all_orders.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    total = len(all_orders)
    total_pages = math.ceil(total / size) if total > 0 else 1
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_items = all_orders[start_idx:end_idx]

    formatted_items = [_format_order(o) for o in page_items]

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
    # Validate package weight
    if order_in.package_weight <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Package weight must be greater than 0",
        )

    # Validate coordinates
    for lat, lng, label in [
        (order_in.pickup_latitude, order_in.pickup_longitude, "Pickup"),
        (order_in.delivery_latitude, order_in.delivery_longitude, "Delivery"),
    ]:
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{label} coordinates out of valid range",
            )

    # Validate foreign keys
    if order_in.customer_id not in SEED_CUSTOMERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer '{order_in.customer_id}' does not exist",
        )

    if order_in.warehouse_id not in SEED_WAREHOUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Warehouse '{order_in.warehouse_id}' does not exist",
        )

    if order_in.assigned_driver_id and order_in.assigned_driver_id not in SEED_DRIVERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver '{order_in.assigned_driver_id}' does not exist",
        )

    # Validate unique order number
    for o in SEED_ORDERS.values():
        if o["order_number"] == order_in.order_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order with order number '{order_in.order_number}' already exists",
            )

    new_id = f"ord-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_order = {
        "id": new_id,
        "order_number": order_in.order_number,
        "customer_id": order_in.customer_id,
        "warehouse_id": order_in.warehouse_id,
        "pickup_latitude": order_in.pickup_latitude,
        "pickup_longitude": order_in.pickup_longitude,
        "delivery_latitude": order_in.delivery_latitude,
        "delivery_longitude": order_in.delivery_longitude,
        "package_weight": order_in.package_weight,
        "priority": order_in.priority.value,
        "delivery_window_start": order_in.delivery_window_start or now,
        "delivery_window_end": order_in.delivery_window_end or now,
        "status": order_in.status.value,
        "assigned_driver_id": order_in.assigned_driver_id,
        "created_at": now,
        "updated_at": now,
    }

    if await check_db_connection():
        try:
            db_o = Order(**new_order)
            db.add(db_o)
            await db.commit()
            await db.refresh(db_o)
        except Exception:
            pass

    SEED_ORDERS[new_id] = new_order

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
            "priority": order_in.priority.value,
        },
        db=db,
    )

    return _format_order(new_order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single order details."""
    o = SEED_ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # If Driver role, verify assignment
    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = _get_driver_id_for_user(current_user.id)
        if o.get("assigned_driver_id") != user_driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this order",
            )

    return _format_order(o)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_in: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update order details or status."""
    o = SEED_ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = o.get("status")

    # Driver role can update status of their assigned orders
    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = _get_driver_id_for_user(current_user.id)
        if o.get("assigned_driver_id") != user_driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update status for orders assigned to you",
            )
        if order_in.status:
            o["status"] = order_in.status.value
    else:
        # Admin / Manager full update
        if order_in.order_number and order_in.order_number != o.get("order_number"):
            for oid, other_o in SEED_ORDERS.items():
                if oid != order_id and other_o.get("order_number") == order_in.order_number:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Order number already exists",
                    )
            o["order_number"] = order_in.order_number

        if order_in.customer_id:
            if order_in.customer_id not in SEED_CUSTOMERS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer does not exist",
                )
            o["customer_id"] = order_in.customer_id

        if order_in.warehouse_id:
            if order_in.warehouse_id not in SEED_WAREHOUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Warehouse does not exist",
                )
            o["warehouse_id"] = order_in.warehouse_id

        if order_in.assigned_driver_id is not None:
            if order_in.assigned_driver_id and order_in.assigned_driver_id not in SEED_DRIVERS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Driver does not exist",
                )
            o["assigned_driver_id"] = order_in.assigned_driver_id

        if order_in.package_weight is not None:
            if order_in.package_weight <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Package weight must be greater than 0",
                )
            o["package_weight"] = order_in.package_weight

        if order_in.pickup_latitude is not None:
            o["pickup_latitude"] = order_in.pickup_latitude
        if order_in.pickup_longitude is not None:
            o["pickup_longitude"] = order_in.pickup_longitude
        if order_in.delivery_latitude is not None:
            o["delivery_latitude"] = order_in.delivery_latitude
        if order_in.delivery_longitude is not None:
            o["delivery_longitude"] = order_in.delivery_longitude

        if order_in.priority:
            o["priority"] = order_in.priority.value
        if order_in.status:
            o["status"] = order_in.status.value
        if order_in.delivery_window_start:
            o["delivery_window_start"] = order_in.delivery_window_start
        if order_in.delivery_window_end:
            o["delivery_window_end"] = order_in.delivery_window_end

    o["updated_at"] = datetime.utcnow()
    SEED_ORDERS[order_id] = o

    action_name = "ORDER_STATUS_CHANGE" if order_in.status and order_in.status.value != old_status else "ORDER_UPDATE"
    await audit_service.log_event(
        action=action_name,
        user=current_user,
        resource_type="ORDER",
        resource_id=order_id,
        success=True,
        details={
            "order_number": o.get("order_number"),
            "old_status": old_status,
            "new_status": o.get("status"),
        },
        db=db,
    )

    return _format_order(o)


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(
    order_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete order (Admin/Manager only)."""
    if order_id not in SEED_ORDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    deleted_ord = SEED_ORDERS[order_id]
    del SEED_ORDERS[order_id]

    await audit_service.log_event(
        action="ORDER_DELETE",
        user=current_user,
        resource_type="ORDER",
        resource_id=order_id,
        success=True,
        details={"order_number": deleted_ord.get("order_number")},
        db=db,
    )

    return {"status": "success", "message": f"Order {order_id} deleted successfully"}
