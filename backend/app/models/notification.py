import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class AlertType(str, enum.Enum):
    MAINTENANCE_DUE = "MAINTENANCE_DUE"
    VEHICLE_OVERLOADED = "VEHICLE_OVERLOADED"
    DRIVER_UNAVAILABLE = "DRIVER_UNAVAILABLE"
    DELIVERY_DELAYED = "DELIVERY_DELAYED"
    ROUTE_EXCEEDS_MAX_DISTANCE = "ROUTE_EXCEEDS_MAX_DISTANCE"
    URGENT_ORDER_UNASSIGNED = "URGENT_ORDER_UNASSIGNED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_role = Column(String(30), nullable=True, index=True)  # ADMIN, LOGISTICS_MANAGER, DRIVER, or ALL
    driver_id = Column(String(36), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    vehicle_id = Column(String(36), nullable=True, index=True)
    route_id = Column(String(36), nullable=True, index=True)
    order_id = Column(String(36), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=False, default=AlertType.SYSTEM_ALERT.value, index=True)
    severity = Column(String(20), nullable=False, default=AlertSeverity.INFO.value, index=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    driver = relationship("Driver", foreign_keys=[driver_id])
