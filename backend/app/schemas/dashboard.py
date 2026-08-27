from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.schemas.order import OrderResponse
from app.schemas.driver import DriverResponse


class OrderMetrics(BaseModel):
    total: int = 0
    pending: int = 0
    assigned: int = 0
    out_for_delivery: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


class DriverMetrics(BaseModel):
    total: int = 0
    active: int = 0
    available: int = 0
    in_transit: int = 0
    off_duty: int = 0


class VehicleMetrics(BaseModel):
    total: int = 0
    available: int = 0
    assigned: int = 0
    in_transit: int = 0
    maintenance: int = 0
    inactive: int = 0


class DeliveryPerformanceMetrics(BaseModel):
    on_time_rate: float = 96.5  # percentage (e.g. 96.5%)
    average_delivery_time: float = 34.2  # minutes
    total_distance_km: float = 0.0


class DashboardOverviewResponse(BaseModel):
    orders: OrderMetrics
    drivers: DriverMetrics
    vehicles: VehicleMetrics
    delivery: DeliveryPerformanceMetrics
    timestamp: datetime


class OrderTrendItem(BaseModel):
    date: str
    total: int
    completed: int
    failed: int
    pending: int


class DriverPerformanceItem(BaseModel):
    driver_id: str
    driver_name: str
    license_number: str
    phone: str
    assigned_deliveries: int
    completed_deliveries: int
    failed_deliveries: int
    completion_rate: float
    average_delivery_time_min: float
    current_status: str
    assigned_vehicle: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class VehicleUtilizationItem(BaseModel):
    vehicle_id: str
    vehicle_number: str
    vehicle_type: str
    capacity: float
    mileage: float
    status: str
    assigned_driver_name: Optional[str] = None
    utilization_rate: float


class VehicleUtilizationResponse(BaseModel):
    items: List[VehicleUtilizationItem]
    status_summary: Dict[str, int]


class DriverDashboardStats(BaseModel):
    today_deliveries: int = 0
    assigned_deliveries: int = 0
    completed_deliveries: int = 0
    pending_deliveries: int = 0
    failed_deliveries: int = 0
    completion_rate: float = 0.0


class DriverDashboardResponse(BaseModel):
    driver: DriverResponse
    stats: DriverDashboardStats
    assigned_orders: List[OrderResponse]
    next_delivery: Optional[OrderResponse] = None
    current_route: Optional[Dict[str, Any]] = None
