from app.core.database import Base
from app.models.user import User, UserRole
from app.models.driver import Driver, DriverStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.warehouse import Warehouse
from app.models.customer import Customer
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.route import (
    Route,
    RouteStop,
    DeliveryEvent,
    OptimizationJob,
    RouteStatus,
    RouteStopStatus,
    DeliveryEventType,
)
from app.models.logistics import DeliveryPoint, DeliveryStatus
from app.models.location import DriverLocation
from app.models.maintenance import VehicleMaintenance, MaintenanceType, MaintenanceStatus
from app.models.notification import Notification, AlertType, AlertSeverity
from app.models.audit_log import AuditLog
from app.models.ai_recommendation import AIRecommendation, RecommendationType, RecommendationStatus

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Driver",
    "DriverStatus",
    "DriverLocation",
    "Vehicle",
    "VehicleStatus",
    "Warehouse",
    "Customer",
    "Order",
    "OrderStatus",
    "OrderPriority",
    "Route",
    "RouteStop",
    "DeliveryEvent",
    "OptimizationJob",
    "RouteStatus",
    "RouteStopStatus",
    "DeliveryEventType",
    "DeliveryPoint",
    "DeliveryStatus",
    "VehicleMaintenance",
    "MaintenanceType",
    "MaintenanceStatus",
    "Notification",
    "AlertType",
    "AlertSeverity",
    "AuditLog",
    "AIRecommendation",
    "RecommendationType",
    "RecommendationStatus",
]
