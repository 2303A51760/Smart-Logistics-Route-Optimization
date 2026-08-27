from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.notification import AlertType, AlertSeverity


class NotificationBase(BaseModel):
    recipient_user_id: Optional[str] = None
    recipient_role: Optional[str] = None
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    route_id: Optional[str] = None
    order_id: Optional[str] = None
    title: str
    message: str
    alert_type: AlertType = AlertType.SYSTEM_ALERT
    severity: AlertSeverity = AlertSeverity.INFO


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationSummaryResponse(BaseModel):
    total_notifications: int
    unread_count: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]


class AlertCheckResult(BaseModel):
    total_alerts_generated: int
    alerts: List[NotificationResponse]
    details: Dict[str, int]
