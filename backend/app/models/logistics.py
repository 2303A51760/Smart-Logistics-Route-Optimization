import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
)
import enum
from app.core.database import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class DeliveryPoint(Base):
    __tablename__ = "delivery_points"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(100), unique=True, nullable=False)
    customer_name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    demand_weight_kg = Column(Float, default=10.0)
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    status = Column(String(20), default=DeliveryStatus.PENDING.value)
    priority = Column(Integer, default=1)  # 1 = Normal, 2 = High, 3 = Urgent
    created_at = Column(DateTime, default=datetime.utcnow)

    route_id = Column(String(36), ForeignKey("routes.id"), nullable=True)
