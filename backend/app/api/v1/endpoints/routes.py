import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db, check_db_connection
from app.models.user import User, UserRole
from app.schemas.route import (
    RouteResponse,
    RouteListResponse,
    RouteStopResponse,
    RouteStopListResponse,
    DeliveryEventResponse,
    DriverActionRequest,
)
from app.core.logistics_store import (
    SEED_ROUTES,
    SEED_ROUTE_STOPS,
    SEED_DELIVERY_EVENTS,
    SEED_DRIVERS,
    SEED_VEHICLES,
    SEED_WAREHOUSES,
    SEED_ORDERS,
    SEED_CUSTOMERS,
)
from app.services.audit_service import audit_service

router = APIRouter()


def _format_stop(s: dict) -> dict:
    ord_item = SEED_ORDERS.get(s.get("order_id"))
    cust_item = SEED_CUSTOMERS.get(ord_item.get("customer_id")) if ord_item else None

    return {
        "id": s["id"],
        "route_id": s["route_id"],
        "order_id": s.get("order_id"),
        "sequence": s.get("sequence", 1),
        "estimated_arrival": s.get("estimated_arrival"),
        "actual_arrival": s.get("actual_arrival"),
        "status": s.get("status", "PENDING"),
        "created_at": s.get("created_at", datetime.utcnow()),
        "completed_at": s.get("completed_at"),
        "order_number": ord_item.get("order_number") if ord_item else None,
        "customer_name": cust_item.get("name") if cust_item else "Client",
        "delivery_address": cust_item.get("address") if cust_item else "Destination",
        "delivery_latitude": ord_item.get("delivery_latitude") if ord_item else None,
        "delivery_longitude": ord_item.get("delivery_longitude") if ord_item else None,
        "package_weight": ord_item.get("package_weight") if ord_item else None,
        "priority": ord_item.get("priority", "NORMAL") if ord_item else "NORMAL",
    }


def _format_route(r: dict) -> dict:
    route_id = r["id"]
    driver = SEED_DRIVERS.get(r.get("driver_id"))
    driver_name = f"Driver {driver['license_number']}" if driver else None

    vehicle = SEED_VEHICLES.get(r.get("vehicle_id"))
    vehicle_number = vehicle.get("vehicle_number") if vehicle else None

    wh = SEED_WAREHOUSES.get(r.get("warehouse_id"))
    wh_name = wh.get("name") if wh else None

    # Gather stops
    stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    stops.sort(key=lambda x: x.get("sequence", 0))

    stops_list = []
    completed_count = 0

    for s in stops:
        if s.get("status") in ["DELIVERED", "FAILED", "SKIPPED"]:
            completed_count += 1
        stops_list.append(_format_stop(s))

    return {
        "id": r["id"],
        "name": r.get("name") or f"Route #{r['id'][:8]}",
        "driver_id": r.get("driver_id"),
        "driver_name": driver_name,
        "vehicle_id": r.get("vehicle_id"),
        "vehicle_number": vehicle_number,
        "warehouse_id": r.get("warehouse_id"),
        "warehouse_name": wh_name,
        "total_distance": r.get("total_distance", 0.0),
        "estimated_duration": r.get("estimated_duration", 0.0),
        "optimization_score": r.get("optimization_score", 100.0),
        "status": r.get("status", "PLANNED"),
        "created_at": r.get("created_at", datetime.utcnow()),
        "started_at": r.get("started_at"),
        "completed_at": r.get("completed_at"),
        "stops_count": len(stops),
        "completed_stops_count": completed_count,
        "stops": stops_list,
    }


def _get_driver_id_for_user(user_id: str) -> Optional[str]:
    for did, d in SEED_DRIVERS.items():
        if d.get("user_id") == user_id:
            return did
    return None


def _check_driver_access(r: dict, current_user: User):
    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = _get_driver_id_for_user(current_user.id)
        if r.get("driver_id") != user_driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access: Drivers can only view and manage their own assigned routes.",
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
    all_routes = list(SEED_ROUTES.values())

    if current_user.role == UserRole.DRIVER.value:
        user_driver_id = _get_driver_id_for_user(current_user.id)
        all_routes = [r for r in all_routes if r.get("driver_id") == user_driver_id]
    elif driver_id:
        all_routes = [r for r in all_routes if r.get("driver_id") == driver_id]

    if status:
        all_routes = [r for r in all_routes if r.get("status") == status]

    all_routes.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    total = len(all_routes)
    paged = all_routes[skip : skip + limit]

    return {
        "total": total,
        "items": [_format_route(r) for r in paged],
    }


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single route details and stops."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)
    return _format_route(r)


@router.get("/{route_id}/stops", response_model=RouteStopListResponse)
async def get_route_stops(
    route_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ordered stops for a specific route."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    stops.sort(key=lambda x: x.get("sequence", 0))

    formatted_stops = [_format_stop(s) for s in stops]
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
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") != "PLANNED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start route in '{r.get('status')}' state. Must be in 'PLANNED' state.",
        )

    now = datetime.utcnow()
    r["status"] = "IN_PROGRESS"
    r["started_at"] = now

    driver_id = r.get("driver_id")
    if driver_id and driver_id in SEED_DRIVERS:
        SEED_DRIVERS[driver_id]["status"] = "IN_TRANSIT"
        if action and action.latitude and action.longitude:
            SEED_DRIVERS[driver_id]["current_latitude"] = action.latitude
            SEED_DRIVERS[driver_id]["current_longitude"] = action.longitude

    # Synchronize all assigned orders on this route to OUT_FOR_DELIVERY
    route_stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    for s in route_stops:
        ord_id = s.get("order_id")
        if ord_id and ord_id in SEED_ORDERS:
            SEED_ORDERS[ord_id]["status"] = "OUT_FOR_DELIVERY"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "driver_id": driver_id,
        "event_type": "ROUTE_STARTED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"notes": action.notes if action else "Route started"},
    })

    await audit_service.log_event(
        action="ROUTE_START",
        user=current_user,
        resource_type="ROUTE",
        resource_id=route_id,
        success=True,
        details={"driver_id": driver_id, "route_name": r.get("name")},
        db=db,
    )

    return _format_route(r)


@router.post("/{route_id}/cancel", response_model=RouteResponse)
async def cancel_route(
    route_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel route: PLANNED/STARTED/IN_PROGRESS -> CANCELLED. Cannot cancel COMPLETED routes."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed route.",
        )

    if r.get("status") == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Route is already cancelled.",
        )

    now = datetime.utcnow()
    r["status"] = "CANCELLED"

    driver_id = r.get("driver_id")
    if driver_id and driver_id in SEED_DRIVERS:
        SEED_DRIVERS[driver_id]["status"] = "AVAILABLE"

    # Reset incomplete orders
    route_stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    for s in route_stops:
        if s.get("status") in ["PENDING", "ARRIVED", "IN_PROGRESS"]:
            s["status"] = "SKIPPED"
            ord_id = s.get("order_id")
            if ord_id and ord_id in SEED_ORDERS and SEED_ORDERS[ord_id]["status"] in ["OUT_FOR_DELIVERY", "ARRIVED", "ASSIGNED"]:
                SEED_ORDERS[ord_id]["status"] = "CANCELLED"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "driver_id": driver_id,
        "event_type": "ROUTE_CANCELLED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"reason": action.reason if action and action.reason else "Route cancelled"},
    })

    await audit_service.log_event(
        action="ROUTE_CANCEL",
        user=current_user,
        resource_type="ROUTE",
        resource_id=route_id,
        success=True,
        details={"driver_id": driver_id, "reason": action.reason if action else "Cancelled by user"},
        db=db,
    )

    return _format_route(r)


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
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record arrival on route in '{r.get('status')}' state. Route must be active.",
        )

    stop = SEED_ROUTE_STOPS.get(stop_id)
    if not stop or stop.get("route_id") != route_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.get("status") != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition from '{stop.get('status')}' to 'ARRIVED'. Must be 'PENDING'.",
        )

    now = datetime.utcnow()
    stop["status"] = "ARRIVED"
    stop["actual_arrival"] = now

    ord_id = stop.get("order_id")
    if ord_id and ord_id in SEED_ORDERS:
        SEED_ORDERS[ord_id]["status"] = "ARRIVED"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "order_id": ord_id,
        "driver_id": r.get("driver_id"),
        "event_type": "ARRIVED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"notes": action.notes if action else None},
    })

    return _format_route(r)


@router.post("/{route_id}/stops/{stop_id}/start-delivery", response_model=RouteResponse)
async def start_delivery_for_stop(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver starts delivery handing-off process: ARRIVED -> IN_PROGRESS."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start delivery on route in '{r.get('status')}' state. Route must be active.",
        )

    stop = SEED_ROUTE_STOPS.get(stop_id)
    if not stop or stop.get("route_id") != route_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.get("status") not in ["ARRIVED", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start delivery for stop in '{stop.get('status')}' state.",
        )

    now = datetime.utcnow()
    stop["status"] = "IN_PROGRESS"
    if not stop.get("actual_arrival"):
        stop["actual_arrival"] = now

    ord_id = stop.get("order_id")
    if ord_id and ord_id in SEED_ORDERS:
        SEED_ORDERS[ord_id]["status"] = "OUT_FOR_DELIVERY"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "order_id": ord_id,
        "driver_id": r.get("driver_id"),
        "event_type": "DELIVERY_STARTED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"notes": action.notes if action else "Delivery handing-off process started"},
    })

    return _format_route(r)


@router.post("/{route_id}/stops/{stop_id}/deliver", response_model=RouteResponse)
async def mark_stop_delivered(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver marks stop delivered: ARRIVED/IN_PROGRESS/PENDING -> DELIVERED. Synchronizes order status to DELIVERED."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deliver stop on route in '{r.get('status')}' state. Route must be active.",
        )

    stop = SEED_ROUTE_STOPS.get(stop_id)
    if not stop or stop.get("route_id") != route_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.get("status") in ["DELIVERED", "FAILED", "SKIPPED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition stop already in '{stop.get('status')}' state.",
        )

    now = datetime.utcnow()
    stop["status"] = "DELIVERED"
    stop["completed_at"] = now
    if not stop.get("actual_arrival"):
        stop["actual_arrival"] = now

    ord_id = stop.get("order_id")
    if ord_id and ord_id in SEED_ORDERS:
        SEED_ORDERS[ord_id]["status"] = "DELIVERED"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "order_id": ord_id,
        "driver_id": r.get("driver_id"),
        "event_type": "DELIVERED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"notes": action.notes if action else "Delivered successfully"},
    })

    # Check if all stops on route finished
    route_stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    all_done = all(s.get("status") in ["DELIVERED", "FAILED", "SKIPPED"] for s in route_stops)
    if all_done:
        r["status"] = "COMPLETED"
        r["completed_at"] = now
        drv_id = r.get("driver_id")
        if drv_id and drv_id in SEED_DRIVERS:
            SEED_DRIVERS[drv_id]["status"] = "AVAILABLE"

        SEED_DELIVERY_EVENTS.append({
            "id": str(uuid.uuid4()),
            "route_id": route_id,
            "driver_id": drv_id,
            "event_type": "ROUTE_COMPLETED",
            "timestamp": now,
            "event_metadata": {"notes": "All stops completed"},
        })

    return _format_route(r)


@router.post("/{route_id}/stops/{stop_id}/fail", response_model=RouteResponse)
async def mark_stop_failed(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver marks stop failed: ARRIVED/IN_PROGRESS/PENDING -> FAILED. Synchronizes order to FAILED."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot fail stop on route in '{r.get('status')}' state. Route must be active.",
        )

    stop = SEED_ROUTE_STOPS.get(stop_id)
    if not stop or stop.get("route_id") != route_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.get("status") in ["DELIVERED", "FAILED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot fail stop already in '{stop.get('status')}' state.",
        )

    # Require failure reason
    failure_reason = (action.reason if action and action.reason else "").strip()
    if not failure_reason:
        failure_reason = "CUSTOMER_UNAVAILABLE"

    now = datetime.utcnow()
    stop["status"] = "FAILED"
    stop["completed_at"] = now
    if not stop.get("actual_arrival"):
        stop["actual_arrival"] = now

    ord_id = stop.get("order_id")
    if ord_id and ord_id in SEED_ORDERS:
        SEED_ORDERS[ord_id]["status"] = "FAILED"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "order_id": ord_id,
        "driver_id": r.get("driver_id"),
        "event_type": "FAILED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"reason": failure_reason, "notes": action.notes if action else None},
    })

    route_stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    all_done = all(s.get("status") in ["DELIVERED", "FAILED", "SKIPPED"] for s in route_stops)
    if all_done:
        r["status"] = "COMPLETED"
        r["completed_at"] = now
        drv_id = r.get("driver_id")
        if drv_id and drv_id in SEED_DRIVERS:
            SEED_DRIVERS[drv_id]["status"] = "AVAILABLE"

        SEED_DELIVERY_EVENTS.append({
            "id": str(uuid.uuid4()),
            "route_id": route_id,
            "driver_id": drv_id,
            "event_type": "ROUTE_COMPLETED",
            "timestamp": now,
            "event_metadata": {"notes": "All stops finished"},
        })

    return _format_route(r)


@router.post("/{route_id}/stops/{stop_id}/skip", response_model=RouteResponse)
async def skip_stop(
    route_id: str,
    stop_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver skips stop: PENDING/ARRIVED -> SKIPPED."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") not in ["IN_PROGRESS", "STARTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot skip stop on route in '{r.get('status')}' state. Route must be active.",
        )

    stop = SEED_ROUTE_STOPS.get(stop_id)
    if not stop or stop.get("route_id") != route_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route stop not found")

    if stop.get("status") in ["DELIVERED", "SKIPPED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot skip stop already in '{stop.get('status')}' state.",
        )

    now = datetime.utcnow()
    stop["status"] = "SKIPPED"
    stop["completed_at"] = now

    skip_reason = action.reason if action and action.reason else "Skipped by driver"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "order_id": stop.get("order_id"),
        "driver_id": r.get("driver_id"),
        "event_type": "SKIPPED",
        "latitude": action.latitude if action else None,
        "longitude": action.longitude if action else None,
        "timestamp": now,
        "event_metadata": {"reason": skip_reason},
    })

    route_stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    all_done = all(s.get("status") in ["DELIVERED", "FAILED", "SKIPPED"] for s in route_stops)
    if all_done:
        r["status"] = "COMPLETED"
        r["completed_at"] = now
        drv_id = r.get("driver_id")
        if drv_id and drv_id in SEED_DRIVERS:
            SEED_DRIVERS[drv_id]["status"] = "AVAILABLE"

        SEED_DELIVERY_EVENTS.append({
            "id": str(uuid.uuid4()),
            "route_id": route_id,
            "driver_id": drv_id,
            "event_type": "ROUTE_COMPLETED",
            "timestamp": now,
            "event_metadata": {"notes": "All stops finished"},
        })

    return _format_route(r)


@router.post("/{route_id}/complete", response_model=RouteResponse)
async def complete_route(
    route_id: str,
    action: Optional[DriverActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicit route completion: disallow completion while pending/in-progress stops remain."""
    r = SEED_ROUTES.get(route_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _check_driver_access(r, current_user)

    if r.get("status") == "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Route is already completed.")

    if r.get("status") == "CANCELLED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot complete a cancelled route.")

    # Validate that all stops are completed (DELIVERED, FAILED, SKIPPED)
    route_stops = [s for s in SEED_ROUTE_STOPS.values() if s.get("route_id") == route_id]
    incomplete_stops = [s for s in route_stops if s.get("status") in ["PENDING", "ARRIVED", "IN_PROGRESS"]]
    if incomplete_stops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete route while {len(incomplete_stops)} stops remain incomplete.",
        )

    now = datetime.utcnow()
    r["status"] = "COMPLETED"
    r["completed_at"] = now

    drv_id = r.get("driver_id")
    if drv_id and drv_id in SEED_DRIVERS:
        SEED_DRIVERS[drv_id]["status"] = "AVAILABLE"

    SEED_DELIVERY_EVENTS.append({
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "driver_id": drv_id,
        "event_type": "ROUTE_COMPLETED",
        "timestamp": now,
        "event_metadata": {"notes": action.notes if action else "Completed"},
    })

    return _format_route(r)
