import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from app.core.database import Base


class AuditLog(Base):
    """Stores persistent, non-repudiable audit trails for operations, security events,
    and administrative actions across the Smart Logistics platform.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    user_role = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., USER_LOGIN, LOGIN_FAILED, ORDER_CREATE, etc.
    resource_type = Column(String(50), nullable=True, index=True)  # e.g., USER, ORDER, ROUTE, VEHICLE
    resource_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    details = Column(Text, nullable=True)  # JSON or descriptive text metadata (sanitized of secrets)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "success": self.success,
            "details": self.details,
        }
