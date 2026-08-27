import json
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import check_db_connection
from app.models.audit_log import AuditLog
from app.models.user import User
from app.core.logistics_store import SEED_AUDIT_LOGS

logger = logging.getLogger(__name__)


def _sanitize_details(details: Any) -> Optional[str]:
    """Sanitizes sensitive fields like passwords, secrets, and bearer tokens before audit storage."""
    if details is None:
        return None
    if isinstance(details, str):
        return details
    if isinstance(details, dict):
        sanitized = {}
        for k, v in details.items():
            if any(secret_key in k.lower() for secret_key in ["password", "token", "secret", "authorization", "hash"]):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v
        return json.dumps(sanitized, default=str)
    return str(details)


class AuditService:
    """Core enterprise audit service managing persistent audit trails and operational security analytics."""

    async def log_event(
        self,
        action: str,
        user: Optional[User] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Any] = None,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Records an audit event to the PostgreSQL database and/or in-memory fallback store."""
        # Resolve user properties
        final_user_id = user.id if user else user_id
        final_user_email = user.email if user else user_email
        final_user_role = user.role if user else user_role

        log_id = f"audit-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        sanitized_details = _sanitize_details(details)

        event_dict = {
            "id": log_id,
            "user_id": final_user_id,
            "user_email": final_user_email,
            "user_role": final_user_role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": now,
            "success": success,
            "details": sanitized_details,
        }

        # 1. Save to DB if available
        if db and await check_db_connection():
            try:
                db_record = AuditLog(
                    id=log_id,
                    user_id=final_user_id,
                    user_email=final_user_email,
                    user_role=final_user_role,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=now,
                    success=success,
                    details=sanitized_details,
                )
                db.add(db_record)
                await db.commit()
            except Exception as e:
                logger.warning(f"Audit log DB commit failed (fallback to store): {e}")

        # 2. Always maintain in in-memory store for instant zero-latency query fallback
        SEED_AUDIT_LOGS[log_id] = event_dict

        return event_dict

    async def get_logs(
        self,
        db: Optional[AsyncSession] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        success: Optional[bool] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[dict], int]:
        """Queries and returns paginated, filtered audit logs."""
        page = max(1, page)
        limit = max(1, min(limit, 200))
        offset = (page - 1) * limit

        # Try database first
        if db and await check_db_connection():
            try:
                query = select(AuditLog)
                count_query = select(func.count(AuditLog.id))

                if user_id:
                    query = query.where(AuditLog.user_id == user_id)
                    count_query = count_query.where(AuditLog.user_id == user_id)
                if action:
                    query = query.where(AuditLog.action == action)
                    count_query = count_query.where(AuditLog.action == action)
                if resource_type:
                    query = query.where(AuditLog.resource_type == resource_type)
                    count_query = count_query.where(AuditLog.resource_type == resource_type)
                if success is not None:
                    query = query.where(AuditLog.success == success)
                    count_query = count_query.where(AuditLog.success == success)
                if start_date:
                    query = query.where(AuditLog.timestamp >= start_date)
                    count_query = count_query.where(AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.where(AuditLog.timestamp <= end_date)
                    count_query = count_query.where(AuditLog.timestamp <= end_date)
                if search:
                    term = f"%{search.lower()}%"
                    search_filter = (
                        func.lower(AuditLog.action).like(term)
                        | func.lower(AuditLog.user_email).like(term)
                        | func.lower(AuditLog.details).like(term)
                    )
                    query = query.where(search_filter)
                    count_query = count_query.where(search_filter)

                total_res = await db.execute(count_query)
                total = total_res.scalar() or 0

                query = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit)
                items_res = await db.execute(query)
                records = [r.to_dict() for r in items_res.scalars().all()]
                return records, total
            except Exception as e:
                logger.warning(f"Audit log DB query failed, falling back to memory store: {e}")

        # Fallback to in-memory store
        items = list(SEED_AUDIT_LOGS.values())
        filtered = []
        for it in items:
            if user_id and it.get("user_id") != user_id:
                continue
            if action and it.get("action") != action:
                continue
            if resource_type and it.get("resource_type") != resource_type:
                continue
            if success is not None and it.get("success") != success:
                continue
            ts = it["timestamp"]
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except Exception:
                    pass
            if isinstance(ts, datetime):
                if start_date and ts < start_date:
                    continue
                if end_date and ts > end_date:
                    continue
            if search:
                term = search.lower()
                action_str = str(it.get("action", "")).lower()
                email_str = str(it.get("user_email", "")).lower()
                details_str = str(it.get("details", "")).lower()
                if term not in action_str and term not in email_str and term not in details_str:
                    continue
            filtered.append(it)

        # Sort newest first
        filtered.sort(
            key=lambda x: x["timestamp"] if isinstance(x["timestamp"], datetime) else datetime.min,
            reverse=True,
        )
        total = len(filtered)
        paged = filtered[offset : offset + limit]
        return paged, total

    async def get_summary(self, db: Optional[AsyncSession] = None) -> dict:
        """Calculates aggregated security metrics and KPI analytics."""
        all_logs = list(SEED_AUDIT_LOGS.values())

        # If DB available, we can fetch all or merge
        total_events = len(all_logs)
        successful_events = sum(1 for x in all_logs if x.get("success") is True)
        failed_events = sum(1 for x in all_logs if x.get("success") is False)
        unauthorized_attempts = sum(
            1 for x in all_logs if not x.get("success") or "UNAUTHORIZED" in str(x.get("action", "")) or "LOGIN_FAILED" in str(x.get("action", ""))
        )

        actions_by_role: Dict[str, int] = {
            "ADMIN": 0,
            "LOGISTICS_MANAGER": 0,
            "DRIVER": 0,
            "UNAUTHENTICATED": 0,
        }
        action_counts: Dict[str, int] = {}

        for x in all_logs:
            r = x.get("user_role") or "UNAUTHENTICATED"
            actions_by_role[r] = actions_by_role.get(r, 0) + 1
            
            act = x.get("action", "UNKNOWN")
            action_counts[act] = action_counts.get(act, 0) + 1

        top_actions = [{"action": act, "count": cnt} for act, cnt in sorted(action_counts.items(), key=lambda i: i[1], reverse=True)[:5]]

        # Recent security-specific events (failed or auth actions)
        recent_security = [
            x for x in all_logs if not x.get("success") or "AUTH" in str(x.get("resource_type", "")) or "LOGIN" in str(x.get("action", ""))
        ]
        recent_security.sort(
            key=lambda x: x["timestamp"] if isinstance(x["timestamp"], datetime) else datetime.min,
            reverse=True,
        )

        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": failed_events,
            "unauthorized_attempts": unauthorized_attempts,
            "actions_by_role": actions_by_role,
            "top_actions": top_actions,
            "recent_security_events": recent_security[:10],
            "generated_at": datetime.utcnow(),
        }


audit_service = AuditService()
