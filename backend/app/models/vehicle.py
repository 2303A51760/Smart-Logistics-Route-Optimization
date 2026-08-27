import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"
    # Backward-compatibility aliases with Phase 1
    IDLE = "AVAILABLE"
    EN_ROUTE = "IN_TRANSIT"
    OFFLINE = "INACTIVE"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=True)
    vehicle_number = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False, default="VAN")
    capacity = Column(Float, nullable=False, default=1000.0)
    fuel_type = Column(String(30), nullable=False, default="DIESEL")
    mileage = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), default=VehicleStatus.AVAILABLE.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="vehicles")
    maintenance_records = relationship("VehicleMaintenance", back_populates="vehicle", cascade="all, delete-orphan")
