import uuid
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class RouteStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RouteStopStatus(str, enum.Enum):
    PENDING = "PENDING"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class DeliveryEventType(str, enum.Enum):
    ROUTE_STARTED = "ROUTE_STARTED"
    ARRIVED = "ARRIVED"
    STOP_ARRIVED = "STOP_ARRIVED"
    DELIVERY_STARTED = "DELIVERY_STARTED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DELIVERY_FAILED = "DELIVERY_FAILED"
    SKIPPED = "SKIPPED"
    STOP_SKIPPED = "STOP_SKIPPED"
    ROUTE_COMPLETED = "ROUTE_COMPLETED"


class Route(Base):
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=True, default="Optimized Route")
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True)
    total_distance = Column(Float, default=0.0)
    estimated_duration = Column(Float, default=0.0)
    optimization_score = Column(Float, default=100.0)
    status = Column(String(30), default=RouteStatus.PLANNED.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    driver = relationship("Driver", backref="routes")
    vehicle = relationship("Vehicle", backref="routes")
    warehouse = relationship("Warehouse", backref="routes")
    stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.sequence")
    events = relationship("DeliveryEvent", back_populates="route", cascade="all, delete-orphan")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=True)
    sequence = Column(Integer, nullable=False, default=1)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    status = Column(String(30), default=RouteStopStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    route = relationship("Route", back_populates="stops")
    order = relationship("Order", backref="route_stops")


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=True)
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=True)
    route_id = Column(String(36), ForeignKey("routes.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_metadata = Column(JSON, nullable=True)

    # Relationships
    order = relationship("Order", backref="delivery_events")
    driver = relationship("Driver", backref="delivery_events")
    route = relationship("Route", back_populates="events")


class OptimizationJob(Base):
    __tablename__ = "optimization_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(30), default="PENDING", nullable=False)
    parameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    optimization_score = Column(Float, default=0.0)
    total_distance_km = Column(Float, default=0.0)
    total_duration_min = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
