import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DriverStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    OFF_DUTY = "OFF_DUTY"
    INACTIVE = "INACTIVE"


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=False)
    status = Column(String(30), default=DriverStatus.AVAILABLE.value, nullable=False)
    current_latitude = Column(Float, nullable=True, default=40.7128)
    current_longitude = Column(Float, nullable=True, default=-74.0060)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="driver_profile")
    vehicles = relationship("Vehicle", back_populates="driver")
    orders = relationship("Order", back_populates="assigned_driver")
