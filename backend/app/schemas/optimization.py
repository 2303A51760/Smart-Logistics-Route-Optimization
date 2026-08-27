from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    warehouse_id: str
    order_ids: List[str]
    driver_ids: Optional[List[str]] = Field(default_factory=list)
    vehicle_ids: Optional[List[str]] = Field(default_factory=list)
    max_route_distance_km: Optional[float] = 250.0
    average_speed_kmh: Optional[float] = 40.0
    time_limit_seconds: Optional[int] = 5


class RouteStopItem(BaseModel):
    sequence: int
    stop_type: str  # DEPOT, DELIVERY
    order_id: Optional[str] = None
    name: str
    latitude: float
    longitude: float
    demand_kg: float
    priority: str
    estimated_arrival_minutes: float


class VehicleRouteItem(BaseModel):
    vehicle_id: str
    vehicle_name: Optional[str] = None
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    total_distance_km: float
    estimated_duration_min: float
    capacity_kg: float
    total_load_kg: float
    stops_count: int
    stops: List[RouteStopItem]


class UnassignedOrderItem(BaseModel):
    order_id: str
    name: str
    latitude: float
    longitude: float
    demand_kg: float
    priority: str
    reason: str


class OptimizationResultResponse(BaseModel):
    job_id: str
    status: str
    solver: Optional[str] = None
    total_distance_km: float
    total_duration_min: float
    vehicles_used: int
    orders_assigned: int
    orders_unassigned: int
    optimization_score: float
    routes: List[VehicleRouteItem]
    unassigned_orders: List[UnassignedOrderItem] = Field(default_factory=list)


class OptimizationJobResponse(BaseModel):
    id: str
    status: str
    optimization_score: float
    total_distance_km: float
    total_duration_min: float
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CreateRoutesFromOptimizationRequest(BaseModel):
    job_id: str
    selected_vehicle_ids: Optional[List[str]] = None
