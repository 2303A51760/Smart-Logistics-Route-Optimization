from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# Vehicle Schemas
class VehicleBase(BaseModel):
    name: str = Field(..., example="Van Alpha-1")
    license_plate: str = Field(..., example="NY-893-TR")
    capacity_kg: float = Field(default=1000.0, ge=1.0)
    current_lat: float = Field(default=40.7128)
    current_lng: float = Field(default=-74.0060)
    status: str = Field(default="IDLE")
    fuel_level_percent: float = Field(default=100.0, ge=0.0, le=100.0)
    is_active: bool = True


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    capacity_kg: Optional[float] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    status: Optional[str] = None
    fuel_level_percent: Optional[float] = None
    is_active: Optional[bool] = None


class VehicleResponse(VehicleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Delivery Point Schemas
class DeliveryPointBase(BaseModel):
    order_id: str = Field(..., example="ORD-10023")
    customer_name: str = Field(..., example="Acme Corp")
    address: str = Field(..., example="350 5th Ave, New York, NY")
    lat: float = Field(..., example=40.7484)
    lng: float = Field(..., example=-73.9857)
    demand_weight_kg: float = Field(default=15.0)
    status: str = Field(default="PENDING")
    priority: int = Field(default=1, ge=1, le=3)


class DeliveryPointCreate(DeliveryPointBase):
    pass


class DeliveryPointResponse(DeliveryPointBase):
    id: str
    route_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Route Schemas
class Waypoint(BaseModel):
    lat: float
    lng: float
    name: Optional[str] = None
    stop_number: int
    demand_kg: Optional[float] = 0.0


class RouteBase(BaseModel):
    name: str = Field(..., example="Downtown Express Route")
    start_lat: float = Field(default=40.7128)
    start_lng: float = Field(default=-74.0060)
    vehicle_id: Optional[str] = None


class RouteCreate(RouteBase):
    deliveries: Optional[List[str]] = []  # IDs of delivery points


class RouteResponse(RouteBase):
    id: str
    total_distance_km: float
    estimated_duration_min: float
    waypoints_json: Optional[List[Dict[str, Any]]] = None
    is_optimized: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Optimization Schemas
class OptimizationRequest(BaseModel):
    vehicle_ids: List[str]
    delivery_ids: List[str]
    depot_lat: float = 40.7128
    depot_lng: float = -74.0060
    max_vehicle_capacity_kg: Optional[float] = 1000.0


class OptimizationResult(BaseModel):
    job_id: str
    status: str
    num_vehicles: int
    num_stops: int
    total_distance_km: float
    estimated_total_time_min: float
    routes: List[Dict[str, Any]]
