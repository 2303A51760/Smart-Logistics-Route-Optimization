from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RouteStopResponse(BaseModel):
    id: str
    route_id: str
    order_id: Optional[str] = None
    sequence: int
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    order_number: Optional[str] = None
    customer_name: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    package_weight: Optional[float] = None
    priority: Optional[str] = None

    class Config:
        from_attributes = True


class RouteStopListResponse(BaseModel):
    total: int
    items: List[RouteStopResponse]


class DeliveryEventResponse(BaseModel):
    id: str
    order_id: Optional[str] = None
    driver_id: Optional[str] = None
    route_id: Optional[str] = None
    event_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: datetime
    event_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class RouteResponse(BaseModel):
    id: str
    name: Optional[str] = None
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    vehicle_id: Optional[str] = None
    vehicle_number: Optional[str] = None
    warehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None
    total_distance: float
    estimated_duration: float
    optimization_score: float
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stops_count: Optional[int] = 0
    completed_stops_count: Optional[int] = 0
    stops: Optional[List[RouteStopResponse]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RouteListResponse(BaseModel):
    total: int
    items: List[RouteResponse]


class DriverActionRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    reason: Optional[str] = None

