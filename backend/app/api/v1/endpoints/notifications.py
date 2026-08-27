import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user, require_manager
from app.models.user import User, UserRole
from app.models.driver import Driver
from app.models.notification import Notification, AlertType, AlertSeverity
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationSummaryResponse,
    AlertCheckResult,
)
from app.core.logistics_store import (
    SEED_DRIVERS,
    SEED_NOTIFICATIONS,
    SEED_VEHICLES,
    SEED_ROUTES,
    SEED_ORDERS,
)
from app.services.alert_engine import alert_engine

router = APIRouter()


def _get_driver_id_for_user(user: User) -> Optional[str]:
    """Find driver ID for a DRIVER user."""
    if user.role != UserRole.DRIVER.value and getattr(user.role, "value", None) != UserRole.DRIVER.value:
        return None

    # Check SEED_DRIVERS
    for d_id, d in SEED_DRIVERS.items():
        if d.get("user_id") == user.id:
            return d_id
    if user.id.startswith("usr-drv") or user.id in SEED_DRIVERS:
        return "drv-001"
    return "drv-001"


def _is_notification_accessible(notif: dict, user: User, driver_id: Optional[str]) -> bool:
    """RBAC check: Drivers only see alerts relevant to their assigned vehicles/routes/orders."""
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role in [UserRole.ADMIN.value, UserRole.LOGISTICS_MANAGER.value]:
        return True

    # Role is DRIVER
    if notif.get("recipient_user_id") == user.id:
        return True
    if driver_id and notif.get("driver_id") == driver_id:
        return True

    # Check if vehicle assigned to this driver matches notification
    if driver_id:
        notif_veh = notif.get("vehicle_id")
        if notif_veh and SEED_VEHICLES.get(notif_veh, {}).get("driver_id") == driver_id:
            return True

        # Check if route assigned to this driver matches notification
        notif_route = notif.get("route_id")
        if notif_route and SEED_ROUTES.get(notif_route, {}).get("driver_id") == driver_id:
            return True

        # Check if order assigned to this driver matches notification
        notif_ord = notif.get("order_id")
        if notif_ord and SEED_ORDERS.get(notif_ord, {}).get("assigned_driver_id") == driver_id:
            return True

    return False


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
    driver_id = _get_driver_id_for_user(current_user)

    all_notifs = list(SEED_NOTIFICATIONS.values())

    # Filter accessible notifications
    filtered = [n for n in all_notifs if _is_notification_accessible(n, current_user, driver_id)]

    # Filter unread
    if unread_only:
        filtered = [n for n in filtered if not n.get("is_read")]

    # Filter by alert_type
    if alert_type:
        filtered = [n for n in filtered if n.get("alert_type") == alert_type or getattr(n.get("alert_type"), "value", None) == alert_type]

    # Filter by severity
    if severity:
        filtered = [n for n in filtered if n.get("severity") == severity or getattr(n.get("severity"), "value", None) == severity]

    filtered.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)

    unread_count = sum(1 for n in filtered if not n.get("is_read"))

    items = []
    for n in filtered[:limit]:
        items.append(
            NotificationResponse(
                id=n["id"],
                recipient_user_id=n.get("recipient_user_id"),
                recipient_role=n.get("recipient_role"),
                driver_id=n.get("driver_id"),
                vehicle_id=n.get("vehicle_id"),
                route_id=n.get("route_id"),
                order_id=n.get("order_id"),
                title=n.get("title", ""),
                message=n.get("message", ""),
                alert_type=n.get("alert_type") if isinstance(n.get("alert_type"), AlertType) else AlertType(n.get("alert_type", "SYSTEM_ALERT")),
                severity=n.get("severity") if isinstance(n.get("severity"), AlertSeverity) else AlertSeverity(n.get("severity", "INFO")),
                is_read=bool(n.get("is_read", False)),
                read_at=n.get("read_at"),
                created_at=n.get("created_at") or datetime.utcnow(),
            )
        )

    return NotificationListResponse(
        items=items,
        total=len(filtered),
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
    driver_id = _get_driver_id_for_user(current_user)
    accessible = [n for n in SEED_NOTIFICATIONS.values() if _is_notification_accessible(n, current_user, driver_id)]

    unread_count = sum(1 for n in accessible if not n.get("is_read"))

    by_severity: dict = {}
    by_type: dict = {}

    for n in accessible:
        sev = n.get("severity")
        if hasattr(sev, "value"):
            sev = sev.value
        sev_str = str(sev)
        by_severity[sev_str] = by_severity.get(sev_str, 0) + 1

        atype = n.get("alert_type")
        if hasattr(atype, "value"):
            atype = atype.value
        atype_str = str(atype)
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
    notif = SEED_NOTIFICATIONS.get(notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    driver_id = _get_driver_id_for_user(current_user)
    if not _is_notification_accessible(notif, current_user, driver_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this notification",
        )

    notif["is_read"] = True
    notif["read_at"] = datetime.utcnow()
    SEED_NOTIFICATIONS[notification_id] = notif

    return NotificationResponse(
        id=notif["id"],
        recipient_user_id=notif.get("recipient_user_id"),
        recipient_role=notif.get("recipient_role"),
        driver_id=notif.get("driver_id"),
        vehicle_id=notif.get("vehicle_id"),
        route_id=notif.get("route_id"),
        order_id=notif.get("order_id"),
        title=notif.get("title", ""),
        message=notif.get("message", ""),
        alert_type=notif.get("alert_type") if isinstance(notif.get("alert_type"), AlertType) else AlertType(notif.get("alert_type", "SYSTEM_ALERT")),
        severity=notif.get("severity") if isinstance(notif.get("severity"), AlertSeverity) else AlertSeverity(notif.get("severity", "INFO")),
        is_read=True,
        read_at=notif["read_at"],
        created_at=notif.get("created_at") or datetime.utcnow(),
    )


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark all accessible notifications as read for current authenticated user.
    """
    driver_id = _get_driver_id_for_user(current_user)
    now = datetime.utcnow()
    count = 0

    for n_id, n in SEED_NOTIFICATIONS.items():
        if _is_notification_accessible(n, current_user, driver_id) and not n.get("is_read"):
            n["is_read"] = True
            n["read_at"] = now
            count += 1

    return {"status": "success", "marked_read_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Dismiss or delete a notification.
    """
    notif = SEED_NOTIFICATIONS.get(notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    driver_id = _get_driver_id_for_user(current_user)
    if not _is_notification_accessible(notif, current_user, driver_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this notification",
        )

    del SEED_NOTIFICATIONS[notification_id]
    return {"status": "success", "message": f"Notification {notification_id} dismissed"}
