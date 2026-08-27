import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class MaintenanceType(str, enum.Enum):
    OIL_CHANGE = "OIL_CHANGE"
    TIRE_ROTATION = "TIRE_ROTATION"
    BRAKE_INSPECTION = "BRAKE_INSPECTION"
    ENGINE_SERVICE = "ENGINE_SERVICE"
    BATTERY_CHECK = "BATTERY_CHECK"
    TRANSMISSION_SERVICE = "TRANSMISSION_SERVICE"
    GENERAL_INSPECTION = "GENERAL_INSPECTION"
    OTHER = "OTHER"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class VehicleMaintenance(Base):
    __tablename__ = "vehicle_maintenance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = Column(String(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_type = Column(String(50), nullable=False, default=MaintenanceType.GENERAL_INSPECTION.value)
    maintenance_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    mileage = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    next_maintenance_mileage = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default=MaintenanceStatus.COMPLETED.value)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")
