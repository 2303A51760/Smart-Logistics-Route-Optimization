from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ETAPredictRequest(BaseModel):
    distance_km: float = Field(..., ge=0.01, le=1000.0, description="Journey distance in kilometers")
    package_weight: Optional[float] = Field(1.0, ge=0.0, description="Package payload weight in kg")
    priority: Optional[str] = Field("NORMAL", description="Order priority: LOW, NORMAL, HIGH, URGENT")
    vehicle_type: Optional[str] = Field("VAN", description="Vehicle type: VAN, TRUCK, BIKE, EV")
    number_of_stops: Optional[int] = Field(1, ge=1, description="Total stops in route execution")
    stop_sequence: Optional[int] = Field(1, ge=1, description="Sequence order for this stop")
    hour: Optional[int] = Field(None, ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None


class ETAPredictResponse(BaseModel):
    predicted_duration_minutes: float
    estimated_arrival: str
    source: str = "ML"  # "ML" or "FALLBACK"
    model_version: str = "eta-v1"
    confidence_interval_min: Optional[float] = None
    confidence_interval_max: Optional[float] = None
    reason: Optional[str] = None


class RouteStopETAResponse(BaseModel):
    stop_id: str
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    customer_name: Optional[str] = None
    delivery_address: Optional[str] = None
    sequence: int
    distance_from_prev_km: float
    predicted_duration_minutes: float
    estimated_arrival: str
    source: str = "ML"
    status: str = "PENDING"


class RouteCumulativeETAResponse(BaseModel):
    route_id: str
    route_name: Optional[str] = None
    total_distance_km: float
    total_predicted_duration_minutes: float
    route_estimated_completion: str
    source: str = "ML"
    model_version: str = "eta-v1"
    stops: List[RouteStopETAResponse]


class MLAnalyticsResponse(BaseModel):
    model_version: str
    selected_model: str
    trained_at: Optional[str] = None
    training_samples: int
    features: List[str]
    selected_metrics: Dict[str, float]
    models_evaluated: Optional[Dict[str, Any]] = None
    status: Optional[str] = "READY"
