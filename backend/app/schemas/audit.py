from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    success: bool
    details: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[AuditLogResponse]


class AuditLogSummaryResponse(BaseModel):
    total_events: int
    successful_events: int
    failed_events: int
    unauthorized_attempts: int
    actions_by_role: Dict[str, int]
    top_actions: List[Dict[str, Any]]
    recent_security_events: List[AuditLogResponse]
    generated_at: datetime


class AuditLogCreate(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: bool = True
    details: Optional[Dict[str, Any]] = None
