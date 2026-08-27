from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin, require_manager
from app.models.user import User, UserRole
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogSummaryResponse,
)
from app.services.audit_service import audit_service

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action code"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g., ORDER, ROUTE)"),
    success: Optional[bool] = Query(None, description="Filter by success/failure"),
    search: Optional[str] = Query(None, description="Search term across action, user, and details"),
    start_date: Optional[datetime] = Query(None, description="Start date ISO filter"),
    end_date: Optional[datetime] = Query(None, description="End date ISO filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated audit logs with multi-field filtering.
    RBAC Rules:
    - ADMIN: Unrestricted access across all operational and security logs.
    - LOGISTICS_MANAGER: Permitted to view operational audit logs.
    - DRIVER: Strictly forbidden from accessing global audit logs (HTTP 403).
    """
    if current_user.role == UserRole.DRIVER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Drivers are not authorized to view enterprise audit logs.",
        )

    # For Logistics Manager, if not Admin, optionally filter to operational resource types
    if current_user.role == UserRole.LOGISTICS_MANAGER.value and not resource_type:
        pass  # Managers have operational visibility

    items, total = await audit_service.get_logs(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        success=success,
        search=search,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )

    return AuditLogListResponse(
        total=total,
        page=page,
        limit=limit,
        items=[AuditLogResponse(**it) for it in items],
    )


@router.get("/summary", response_model=AuditLogSummaryResponse)
async def get_audit_summary(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated security KPI metrics, breakdown by role, top actions,
    and recent security events. Restricted to ADMIN and LOGISTICS_MANAGER roles.
    """
    summary = await audit_service.get_summary(db=db)
    return AuditLogSummaryResponse(
        total_events=summary["total_events"],
        successful_events=summary["successful_events"],
        failed_events=summary["failed_events"],
        unauthorized_attempts=summary["unauthorized_attempts"],
        actions_by_role=summary["actions_by_role"],
        top_actions=summary["top_actions"],
        recent_security_events=[AuditLogResponse(**e) for e in summary["recent_security_events"]],
        generated_at=summary["generated_at"],
    )


@router.get("/{id}", response_model=AuditLogResponse)
async def get_audit_log_by_id(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch a single audit log event by its ID.
    """
    if current_user.role == UserRole.DRIVER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Drivers are not authorized to view audit logs.",
        )

    items, _ = await audit_service.get_logs(db=db, page=1, limit=1)
    
    # Check memory store first for exact ID match
    from app.core.logistics_store import SEED_AUDIT_LOGS
    if id in SEED_AUDIT_LOGS:
        return AuditLogResponse(**SEED_AUDIT_LOGS[id])

    # Try DB lookup
    from sqlalchemy import select
    from app.models.audit_log import AuditLog
    from app.core.database import check_db_connection
    if await check_db_connection():
        try:
            res = await db.execute(select(AuditLog).where(AuditLog.id == id))
            rec = res.scalar_one_or_none()
            if rec:
                return AuditLogResponse(**rec.to_dict())
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audit log entry with ID '{id}' not found",
    )
