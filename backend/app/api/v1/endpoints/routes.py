import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.route import Route, RouteStop, DeliveryEvent
from app.models.driver import Driver, DriverStatus
from app.models.vehicle import Vehicle
from app.models.warehouse import Warehouse
from app.models.order import Order, OrderStatus
from app.models.customer import Customer
from app.schemas.route import (
    RouteResponse,
    RouteListResponse,
    RouteStopResponse,
    RouteStopListResponse,
    DriverActionRequest,
)
from app.services.audit_service import audit_service

router = APIRouter()


async def _get_driver_id_for_user(user_id: str, db: AsyncSession) -> Optional[str]:
    stmt = select(Driver.id).where(Driver.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def _check_driver_access(r: Route, current_user: User, db: AsyncSession):
    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = await _get_driver_id_for_user(current_user.id, db)
        if r.driver_id != user_driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access: Drivers can only view and manage their own assigned routes.",
            )


async def _format_stop_db(s: RouteStop, db: AsyncSession) -> RouteStopResponse:
    order = None
    cust = None
    if s.order_id:
        o_res = await db.execute(select(Order).where(Order.id == s.order_id))
        order = o_res.scalar_one_or_none()
        if order and order.customer_id:
            c_res = await db.execute(select(Customer).where(Customer.id == order.customer_id))
            cust = c_res.scalar_one_or_none()

    return RouteStopResponse(
        id=s.id,
        route_id=s.route_id,
        order_id=s.order_id,
        sequence=s.sequence,
        estimated_arrival=s.estimated_arrival,
        actual_arrival=s.actual_arrival,
        status=s.status,
        created_at=s.created_at,
        completed_at=s.completed_at,
        order_number=order.order_number if order else None,
        customer_name=cust.name if cust else "Client",
        delivery_address=cust.address if cust else "Destination",
        delivery_latitude=order.delivery_latitude if order else None,
        delivery_longitude=order.delivery_longitude if order else None,
        package_weight=order.package_weight if order else None,
        priority=order.priority if order else "NORMAL",
    )


async def _format_route_db(r: Route, db: AsyncSession, include_stops: bool = True) -> RouteResponse:
    driver_name = None
    if r.driver_id:
        d_res = await db.execute(select(Driver.license_number).where(Driver.id == r.driver_id))
        lic = d_res.scalar_one_or_none()
        if lic:
            driver_name = f"Driver {lic}"

    vehicle_number = None
    if r.vehicle_id:
        v_res = await db.execute(select(Vehicle.vehicle_number).where(Vehicle.id == r.vehicle_id))
        vehicle_number = v_res.scalar_one_or_none()

    warehouse_name = None
    if r.warehouse_id:
        w_res = await db.execute(select(Warehouse.name).where(Warehouse.id == r.warehouse_id))
        warehouse_name = w_res.scalar_one_or_none()

    s_res = await db.execute(select(RouteStop).where(RouteStop.route_id == r.id).order_by(RouteStop.sequence))
    stops = s_res.scalars().all()

    completed_count = sum(1 for s in stops if s.status in ["DELIVERED", "FAILED", "SKIPPED"])

    formatted_stops = []
    if include_stops and stops:
        order_ids = [s.order_id for s in stops if s.order_id]
        orders_map = {}
        custs_map = {}
        if order_ids:
            ords_res = await db.execute(select(Order).where(Order.id.in_(order_ids)))
            orders = ords_res.scalars().all()
            orders_map = {o.id: o for o in orders}
            cust_ids = [o.customer_id for o in orders if o.customer_id]
            if cust_ids:
                c_res = await db.execute(select(Customer).where(Customer.id.in_(cust_ids)))
                custs = c_res.scalars().all()
                custs_map = {c.id: c for c in custs}

        for s in stops:
            ord_item = orders_map.get(s.order_id)
            cust_item = custs_map.get(ord_item.customer_id) if ord_item and ord_item.customer_id else None
            formatted_stops.append(
                RouteStopResponse(
                    id=s.id,
                    route_id=s.route_id,
                    order_id=s.order_id,
                    sequence=s.sequence,
                    estimated_arrival=s.estimated_arrival,
                    actual_arrival=s.actual_arrival,
                    status=s.status,
                    created_at=s.created_at,
                    completed_at=s.completed_at,
                    order_number=ord_item.order_number if ord_item else None,
                    customer_name=cust_item.name if cust_item else "Client",
                    delivery_address=cust_item.address if cust_item else "Destination",
                    delivery_latitude=ord_item.delivery_latitude if ord_item else None,
                    delivery_longitude=ord_item.delivery_longitude if ord_item else None,
                    package_weight=ord_item.package_weight if ord_item else None,
                    priority=ord_item.priority if ord_item else "NORMAL",
                )
            )

    return RouteResponse(
        id=r.id,
        name=r.name or f"Route #{r.id[:8]}",
        driver_id=r.driver_id,
        driver_name=driver_name,
        vehicle_id=r.vehicle_id,
        vehicle_number=vehicle_number,
        warehouse_id=r.warehouse_id,
        warehouse_name=warehouse_name,
        total_distance=r.total_distance or 0.0,
        estimated_duration=r.estimated_duration or 0.0,
        optimization_score=r.optimization_score or 100.0,
        status=r.status,
        created_at=r.created_at,
        started_at=r.started_at,
        completed_at=r.completed_at,
        stops_count=len(stops),
        completed_stops_count=completed_count,
        stops=formatted_stops,
    )


@router.get("", response_model=RouteListResponse)
async def list_routes(
    status: Optional[str] = Query(None),
    driver_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List routes. Drivers only see their assigned routes; Managers and Admins see all."""
    stmt = select(Route)

    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = await _get_driver_id_for_user(current_user.id, db)
        stmt = stmt.where(Route.driver_id == user_driver_id)
    elif driver_id:
        stmt = stmt.where(Route.driver_id == driver_id)

    if status:
        stmt = stmt.where(Route.status == status)

    count_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_res.scalar() or 0

    paged_res = await db.execute(stmt.order_by(Route.created_at.desc()).offset(skip).limit(limit))
    routes = paged_res.scalars().all()

    items = [await _format_route_db(r, db) for r in routes]

    return {
        "total": total,
        "items": items,
    }


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single route details and stops."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)
    return await _format_route_db(r, db)


@router.get("/{route_id}/stops", response_model=RouteStopListResponse)
async def get_route_stops(
    route_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ordered stops for a specific route."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    s_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.sequence))
    stops = s_res.scalars().all()

    formatted_stops = [await _format_stop_db(s, db) for s in stops]
    return {
        "total": len(formatted_stops),
        "items": formatted_stops,
    }


@router.post("/{route_id}/start", response_model=RouteResponse)
async def start_route(
    route_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver starts route: PLANNED -> IN_PROGRESS / STARTED. Synchronizes orders to OUT_FOR_DELIVERY."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status != "PLANNED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start route in '{r.status}' state. Must be in 'PLANNED' state.",
        )

    now = datetime.utcnow()
    r.status = "IN_PROGRESS"
    r.started_at = now

    driver_id = r.driver_id
    if driver_id:
        d_res = await db.execute(select(Driver).where(Driver.id == driver_id))
        driver = d_res.scalar_one_or_none()
        if driver:
            driver.status = DriverStatus.IN_TRANSIT.value if hasattr(DriverStatus.IN_TRANSIT, "value") else "IN_TRANSIT"
            if action and action.latitude and action.longitude:
                driver.current_latitude = action.latitude
                driver.current_longitude = action.longitude

    # Synchronize all assigned orders on this route to OUT_FOR_DELIVERY
    stops_res = await db.execute(select(RouteStop.order_id).where(RouteStop.route_id == route_id))
    order_ids = [oid for (oid,) in stops_res.all() if oid]
    if order_ids:
        await db.execute(
            update(Order).where(Order.id.in_(order_ids)).values(
                status=OrderStatus.OUT_FOR_DELIVERY.value if hasattr(OrderStatus.OUT_FOR_DELIVERY, "value") else "OUT_FOR_DELIVERY",
                updated_at=now,
            )
        )

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        driver_id=driver_id,
        event_type="ROUTE_STARTED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"notes": action.notes if action else "Route started"},
    )
    db.add(event)
    await db.commit()
    await db.refresh(r)

    await audit_service.log_event(
        action="ROUTE_START",
        user=current_user,
        resource_type="ROUTE",
        resource_id=route_id,
        success=True,
        details={"driver_id": driver_id, "route_name": r.name},
        db=db,
    )

    return await _format_route_db(r, db)


@router.post("/{route_id}/cancel", response_model=RouteResponse)
async def cancel_route(
    route_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel route: PLANNED/STARTED/IN_PROGRESS -> CANCELLED. Cannot cancel COMPLETED routes."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed route.",
        )

    if r.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Route is already cancelled.",
        )

    now = datetime.utcnow()
    r.status = "CANCELLED"

    driver_id = r.driver_id
    if driver_id:
        d_res = await db.execute(select(Driver).where(Driver.id == driver_id))
        driver = d_res.scalar_one_or_none()
        if driver:
            driver.status = DriverStatus.AVAILABLE.value if hasattr(DriverStatus.AVAILABLE, "value") else "AVAILABLE"

    # Reset incomplete stops and orders
    stops_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id))
    route_stops = stops_res.scalars().all()
    incomplete_order_ids = []
    for s in route_stops:
        if s.status in ["PENDING", "ARRIVED", "IN_PROGRESS"]:
            s.status = "SKIPPED"
            s.completed_at = now
            if s.order_id:
                incomplete_order_ids.append(s.order_id)

    if incomplete_order_ids:
        await db.execute(
            update(Order).where(
                Order.id.in_(incomplete_order_ids),
                Order.status.in_(["OUT_FOR_DELIVERY", "ARRIVED", "ASSIGNED"])
            ).values(status="CANCELLED", updated_at=now)
        )

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        driver_id=driver_id,
        event_type="ROUTE_CANCELLED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"reason": action.reason if action and action.reason else "Route cancelled"},
    )
    db.add(event)
    await db.commit()
    await db.refresh(r)

    await audit_service.log_event(
        action="ROUTE_CANCEL",
        user=current_user,
        resource_type="ROUTE",
        resource_id=route_id,
        success=True,
        details={"driver_id": driver_id, "reason": action.reason if action else "Cancelled by user"},
        db=db,
    )

    return await _format_route_db(r, db)


@router.post("/{route_id}/stops/{stop_id}/arrive", response_model=RouteResponse)
@router.post("/{route_id}/stops/{stop_id}/arrived", response_model=RouteResponse)
async def arrive_at_stop(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver arrives at stop: PENDING -> ARRIVED. Synchronizes order status to ARRIVED."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record arrival on route in '{r.status}' state. Route must be active.",
        )

    s_res = await db.execute(select(RouteStop).where(RouteStop.id == stop_id, RouteStop.route_id == route_id))
    stop = s_res.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition from '{stop.status}' to 'ARRIVED'. Must be 'PENDING'.",
        )

    now = datetime.utcnow()
    stop.status = "ARRIVED"
    stop.actual_arrival = now

    if stop.order_id:
        await db.execute(update(Order).where(Order.id == stop.order_id).values(status="ARRIVED", updated_at=now))

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        order_id=stop.order_id,
        driver_id=r.driver_id,
        event_type="ARRIVED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"notes": action.notes if action else None},
    )
    db.add(event)
    await db.commit()
    await db.refresh(r)

    return await _format_route_db(r, db)


@router.post("/{route_id}/stops/{stop_id}/start-delivery", response_model=RouteResponse)
async def start_delivery_for_stop(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver starts delivery handing-off process: ARRIVED -> IN_PROGRESS."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start delivery on route in '{r.status}' state. Route must be active.",
        )

    s_res = await db.execute(select(RouteStop).where(RouteStop.id == stop_id, RouteStop.route_id == route_id))
    stop = s_res.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.status not in ["ARRIVED", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start delivery for stop in '{stop.status}' state.",
        )

    now = datetime.utcnow()
    stop.status = "IN_PROGRESS"
    if not stop.actual_arrival:
        stop.actual_arrival = now

    if stop.order_id:
        await db.execute(update(Order).where(Order.id == stop.order_id).values(status="OUT_FOR_DELIVERY", updated_at=now))

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        order_id=stop.order_id,
        driver_id=r.driver_id,
        event_type="DELIVERY_STARTED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"notes": action.notes if action else "Delivery handing-off process started"},
    )
    db.add(event)
    await db.commit()
    await db.refresh(r)

    return await _format_route_db(r, db)


@router.post("/{route_id}/stops/{stop_id}/deliver", response_model=RouteResponse)
async def mark_stop_delivered(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver marks stop delivered: ARRIVED/IN_PROGRESS/PENDING -> DELIVERED. Synchronizes order status to DELIVERED."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deliver stop on route in '{r.status}' state. Route must be active.",
        )

    s_res = await db.execute(select(RouteStop).where(RouteStop.id == stop_id, RouteStop.route_id == route_id))
    stop = s_res.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.status in ["DELIVERED", "FAILED", "SKIPPED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition stop already in '{stop.status}' state.",
        )

    now = datetime.utcnow()
    stop.status = "DELIVERED"
    stop.completed_at = now
    if not stop.actual_arrival:
        stop.actual_arrival = now

    if stop.order_id:
        await db.execute(update(Order).where(Order.id == stop.order_id).values(status="DELIVERED", updated_at=now))

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        order_id=stop.order_id,
        driver_id=r.driver_id,
        event_type="DELIVERED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"notes": action.notes if action else "Delivered successfully"},
    )
    db.add(event)

    # Check if all stops on route are finished
    all_stops_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id))
    all_stops = all_stops_res.scalars().all()
    all_done = all(s.status in ["DELIVERED", "FAILED", "SKIPPED"] for s in all_stops)
    if all_done:
        r.status = "COMPLETED"
        r.completed_at = now
        if r.driver_id:
            await db.execute(update(Driver).where(Driver.id == r.driver_id).values(status="AVAILABLE"))

        complete_event = DeliveryEvent(
            id=str(uuid.uuid4()),
            route_id=route_id,
            driver_id=r.driver_id,
            event_type="ROUTE_COMPLETED",
            timestamp=now,
            event_metadata={"notes": "All stops completed"},
        )
        db.add(complete_event)

    await db.commit()
    await db.refresh(r)

    return await _format_route_db(r, db)


@router.post("/{route_id}/stops/{stop_id}/fail", response_model=RouteResponse)
async def mark_stop_failed(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver marks stop failed: ARRIVED/IN_PROGRESS/PENDING -> FAILED. Synchronizes order to FAILED."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot fail stop on route in '{r.status}' state. Route must be active.",
        )

    s_res = await db.execute(select(RouteStop).where(RouteStop.id == stop_id, RouteStop.route_id == route_id))
    stop = s_res.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.status in ["DELIVERED", "FAILED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot fail stop already in '{stop.status}' state.",
        )

    failure_reason = (action.reason if action and action.reason else "").strip()
    if not failure_reason:
        failure_reason = "CUSTOMER_UNAVAILABLE"

    now = datetime.utcnow()
    stop.status = "FAILED"
    stop.completed_at = now
    if not stop.actual_arrival:
        stop.actual_arrival = now

    if stop.order_id:
        await db.execute(update(Order).where(Order.id == stop.order_id).values(status="FAILED", updated_at=now))

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        order_id=stop.order_id,
        driver_id=r.driver_id,
        event_type="FAILED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"reason": failure_reason, "notes": action.notes if action else None},
    )
    db.add(event)

    all_stops_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id))
    all_stops = all_stops_res.scalars().all()
    all_done = all(s.status in ["DELIVERED", "FAILED", "SKIPPED"] for s in all_stops)
    if all_done:
        r.status = "COMPLETED"
        r.completed_at = now
        if r.driver_id:
            await db.execute(update(Driver).where(Driver.id == r.driver_id).values(status="AVAILABLE"))

        complete_event = DeliveryEvent(
            id=str(uuid.uuid4()),
            route_id=route_id,
            driver_id=r.driver_id,
            event_type="ROUTE_COMPLETED",
            timestamp=now,
            event_metadata={"notes": "All stops finished"},
        )
        db.add(complete_event)

    await db.commit()
    await db.refresh(r)

    return await _format_route_db(r, db)


@router.post("/{route_id}/stops/{stop_id}/skip", response_model=RouteResponse)
async def skip_stop(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver skips stop: PENDING/ARRIVED -> SKIPPED."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot skip stop on route in '{r.status}' state. Route must be active.",
        )

    s_res = await db.execute(select(RouteStop).where(RouteStop.id == stop_id, RouteStop.route_id == route_id))
    stop = s_res.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.status in ["DELIVERED", "SKIPPED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot skip stop already in '{stop.status}' state.",
        )

    now = datetime.utcnow()
    stop.status = "SKIPPED"
    stop.completed_at = now

    skip_reason = action.reason if action and action.reason else "Skipped by driver"

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        order_id=stop.order_id,
        driver_id=r.driver_id,
        event_type="SKIPPED",
        latitude=action.latitude if action else None,
        longitude=action.longitude if action else None,
        timestamp=now,
        event_metadata={"reason": skip_reason},
    )
    db.add(event)

    all_stops_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id))
    all_stops = all_stops_res.scalars().all()
    all_done = all(s.status in ["DELIVERED", "FAILED", "SKIPPED"] for s in all_stops)
    if all_done:
        r.status = "COMPLETED"
        r.completed_at = now
        if r.driver_id:
            await db.execute(update(Driver).where(Driver.id == r.driver_id).values(status="AVAILABLE"))

        complete_event = DeliveryEvent(
            id=str(uuid.uuid4()),
            route_id=route_id,
            driver_id=r.driver_id,
            event_type="ROUTE_COMPLETED",
            timestamp=now,
            event_metadata={"notes": "All stops finished"},
        )
        db.add(complete_event)

    await db.commit()
    await db.refresh(r)

    return await _format_route_db(r, db)


@router.post("/{route_id}/complete", response_model=RouteResponse)
async def complete_route(
    route_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicit route completion: disallow completion while pending/in-progress stops remain."""
    r_res = await db.execute(select(Route).where(Route.id == route_id))
    r = r_res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    await _check_driver_access(r, current_user, db)

    if r.status == "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Route is already completed.")

    if r.status == "CANCELLED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot complete a cancelled route.")

    all_stops_res = await db.execute(select(RouteStop).where(RouteStop.route_id == route_id))
    route_stops = all_stops_res.scalars().all()
    incomplete_stops = [s for s in route_stops if s.status in ["PENDING", "ARRIVED", "IN_PROGRESS"]]
    if incomplete_stops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete route while {len(incomplete_stops)} stops remain incomplete.",
        )

    now = datetime.utcnow()
    r.status = "COMPLETED"
    r.completed_at = now

    drv_id = r.driver_id
    if drv_id:
        await db.execute(update(Driver).where(Driver.id == drv_id).values(status="AVAILABLE"))

    event = DeliveryEvent(
        id=str(uuid.uuid4()),
        route_id=route_id,
        driver_id=drv_id,
        event_type="ROUTE_COMPLETED",
        timestamp=now,
        event_metadata={"notes": action.notes if action else "Completed"},
    )
    db.add(event)
    await db.commit()
    await db.refresh(r)

    return await _format_route_db(r, db)
