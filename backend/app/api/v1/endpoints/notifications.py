from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, or_

from app.core.database import get_db
from app.api.deps import get_current_user, require_manager
from app.models.user import User, UserRole
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.order import Order
from app.models.notification import Notification, AlertType, AlertSeverity
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationSummaryResponse,
    AlertCheckResult,
)
from app.services.alert_engine import alert_engine

router = APIRouter()


async def _get_driver_accessible_ids(user: User, db: AsyncSession):
    """Find driver_id, vehicle_ids, route_ids, and order_ids for a DRIVER user."""
    res_d = await db.execute(select(Driver.id).where(Driver.user_id == user.id))
    driver_id = res_d.scalar_one_or_none()

    vehicle_ids = []
    route_ids = []
    order_ids = []

    if driver_id:
        res_v = await db.execute(select(Vehicle.id).where(Vehicle.driver_id == driver_id))
        vehicle_ids = res_v.scalars().all()

        res_r = await db.execute(select(Route.id).where(Route.driver_id == driver_id))
        route_ids = res_r.scalars().all()

        res_o = await db.execute(select(Order.id).where(Order.assigned_driver_id == driver_id))
        order_ids = res_o.scalars().all()

    return driver_id, vehicle_ids, route_ids, order_ids


def _build_driver_filter(user: User, driver_id, vehicle_ids, route_ids, order_ids):
    conditions = [
        Notification.recipient_user_id == user.id,
    ]
    if driver_id:
        conditions.append(Notification.driver_id == driver_id)
    if vehicle_ids:
        conditions.append(Notification.vehicle_id.in_(vehicle_ids))
    if route_ids:
        conditions.append(Notification.route_id.in_(route_ids))
    if order_ids:
        conditions.append(Notification.order_id.in_(order_ids))
    return or_(*conditions)


def _format_notification_model(n: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=n.id,
        recipient_user_id=n.recipient_user_id,
        recipient_role=n.recipient_role,
        driver_id=n.driver_id,
        vehicle_id=n.vehicle_id,
        route_id=n.route_id,
        order_id=n.order_id,
        title=n.title or "",
        message=n.message or "",
        alert_type=n.alert_type if isinstance(n.alert_type, AlertType) else AlertType(n.alert_type or "SYSTEM_ALERT"),
        severity=n.severity if isinstance(n.severity, AlertSeverity) else AlertSeverity(n.severity or "INFO"),
        is_read=bool(n.is_read),
        read_at=n.read_at,
        created_at=n.created_at or datetime.utcnow(),
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = False,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List notifications for current authenticated user with RBAC isolation.
    """
    stmt = select(Notification)

    if current_user.role == UserRole.DRIVER.value:
        driver_id, vehicle_ids, route_ids, order_ids = await _get_driver_accessible_ids(current_user, db)
        stmt = stmt.where(_build_driver_filter(current_user, driver_id, vehicle_ids, route_ids, order_ids))

    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))

    if alert_type:
        stmt = stmt.where(Notification.alert_type == alert_type)

    if severity:
        stmt = stmt.where(Notification.severity == severity)

    res = await db.execute(stmt.order_by(desc(Notification.created_at)))
    all_notifs = res.scalars().all()

    unread_count = sum(1 for n in all_notifs if not n.is_read)
    paged = all_notifs[:limit]

    items = [_format_notification_model(n) for n in paged]

    return NotificationListResponse(
        items=items,
        total=len(all_notifs),
        unread_count=unread_count,
    )


@router.get("/summary", response_model=NotificationSummaryResponse)
async def get_notification_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get count of unread notifications, by severity and by alert type.
    """
    stmt = select(Notification)

    if current_user.role == UserRole.DRIVER.value:
        driver_id, vehicle_ids, route_ids, order_ids = await _get_driver_accessible_ids(current_user, db)
        stmt = stmt.where(_build_driver_filter(current_user, driver_id, vehicle_ids, route_ids, order_ids))

    res = await db.execute(stmt)
    accessible = res.scalars().all()

    unread_count = sum(1 for n in accessible if not n.is_read)

    by_severity: dict = {}
    by_type: dict = {}

    for n in accessible:
        sev_str = str(n.severity.value if hasattr(n.severity, "value") else n.severity)
        by_severity[sev_str] = by_severity.get(sev_str, 0) + 1

        atype_str = str(n.alert_type.value if hasattr(n.alert_type, "value") else n.alert_type)
        by_type[atype_str] = by_type.get(atype_str, 0) + 1

    return NotificationSummaryResponse(
        total_notifications=len(accessible),
        unread_count=unread_count,
        by_severity=by_severity,
        by_type=by_type,
    )


@router.post("/check-alerts", response_model=AlertCheckResult)
async def trigger_intelligent_alert_audit(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Runs on-demand intelligent hazard audit across fleet, routes, orders, and maintenance schedules.
    (ADMIN and LOGISTICS_MANAGER only).
    """
    generated = await alert_engine.evaluate_and_generate_alerts(db)

    details: dict = {}
    for a in generated:
        at = a.get("alert_type", "OTHER")
        details[at] = details.get(at, 0) + 1

    alerts_out = [
        NotificationResponse(
            id=a["id"],
            recipient_user_id=a.get("recipient_user_id"),
            recipient_role=a.get("recipient_role"),
            driver_id=a.get("driver_id"),
            vehicle_id=a.get("vehicle_id"),
            route_id=a.get("route_id"),
            order_id=a.get("order_id"),
            title=a.get("title", ""),
            message=a.get("message", ""),
            alert_type=a.get("alert_type") if isinstance(a.get("alert_type"), AlertType) else AlertType(a.get("alert_type", "SYSTEM_ALERT")),
            severity=a.get("severity") if isinstance(a.get("severity"), AlertSeverity) else AlertSeverity(a.get("severity", "INFO")),
            is_read=bool(a.get("is_read", False)),
            read_at=a.get("read_at"),
            created_at=a.get("created_at") or datetime.utcnow(),
        )
        for a in generated
    ]

    return AlertCheckResult(
        total_alerts_generated=len(generated),
        alerts=alerts_out,
        details=details,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a notification as read.
    """
    res = await db.execute(select(Notification).where(Notification.id == notification_id))
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if current_user.role == UserRole.DRIVER.value:
        driver_id, vehicle_ids, route_ids, order_ids = await _get_driver_accessible_ids(current_user, db)
        is_ok = (
            notif.recipient_user_id == current_user.id
            or (driver_id and notif.driver_id == driver_id)
            or (vehicle_ids and notif.vehicle_id in vehicle_ids)
            or (route_ids and notif.route_id in route_ids)
            or (order_ids and notif.order_id in order_ids)
        )
        if not is_ok:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden to this notification",
            )

    notif.is_read = True
    notif.read_at = datetime.utcnow()
    await db.commit()
    await db.refresh(notif)

    return _format_notification_model(notif)


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark all accessible notifications as read for current authenticated user.
    """
    now = datetime.utcnow()
    stmt = update(Notification).where(Notification.is_read.is_(False)).values(is_read=True, read_at=now)

    if current_user.role == UserRole.DRIVER.value:
        driver_id, vehicle_ids, route_ids, order_ids = await _get_driver_accessible_ids(current_user, db)
        stmt = stmt.where(_build_driver_filter(current_user, driver_id, vehicle_ids, route_ids, order_ids))

    result = await db.execute(stmt)
    await db.commit()
    return {"status": "success", "marked_read_count": result.rowcount}


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Dismiss or delete a notification.
    """
    res = await db.execute(select(Notification).where(Notification.id == notification_id))
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if current_user.role == UserRole.DRIVER.value:
        driver_id, vehicle_ids, route_ids, order_ids = await _get_driver_accessible_ids(current_user, db)
        is_ok = (
            notif.recipient_user_id == current_user.id
            or (driver_id and notif.driver_id == driver_id)
            or (vehicle_ids and notif.vehicle_id in vehicle_ids)
            or (route_ids and notif.route_id in route_ids)
            or (order_ids and notif.order_id in order_ids)
        )
        if not is_ok:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden to this notification",
            )

    await db.delete(notif)
    await db.commit()
    return {"status": "success", "message": f"Notification {notification_id} dismissed"}
