from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# -------------------------------------------------------------
# 1. ORDER PRIORITY SCHEMAS
# -------------------------------------------------------------
class OrderPriorityResponse(BaseModel):
    order_id: str
    order_number: Optional[str] = None
    score: float = Field(..., ge=0.0, le=100.0)
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    raw_priority: Optional[str] = "NORMAL"
    factors: Dict[str, Any]
    reasons: List[str]
    recommendation: str
    model_name: str
    model_version: str


class OrderPriorityListResponse(BaseModel):
    total: int
    orders: List[OrderPriorityResponse]


# -------------------------------------------------------------
# 2. DISPATCH ASSIGNMENT SCHEMAS
# -------------------------------------------------------------
class DispatchRecommendationItem(BaseModel):
    order_id: str
    order_number: Optional[str] = None
    driver_id: str
    driver_name: str
    driver_status: Optional[str] = "AVAILABLE"
    vehicle_id: str
    vehicle_name: str
    vehicle_capacity_kg: float
    score: float = Field(..., ge=0.0, le=100.0)
    reasons: List[str]
    model_name: str
    model_version: str


class DispatchRecommendationsResponse(BaseModel):
    recommendations: List[DispatchRecommendationItem]
    total: int


# -------------------------------------------------------------
# 3. DELAY RISK PREDICTION SCHEMAS
# -------------------------------------------------------------
class DelayRiskRequest(BaseModel):
    order_id: str
    distance_km: float = Field(..., gt=0.0)
    stops_count: Optional[int] = 1
    hour_of_day: Optional[int] = 14
    weather_factor: Optional[int] = 1
    traffic_index: Optional[float] = 1.2
    weight_kg: Optional[float] = 5.0
    deadline_minutes_remaining: Optional[float] = None


class DelayRiskResponse(BaseModel):
    order_id: str
    delay_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: str  # LOW, MEDIUM, HIGH
    predicted_delay_minutes: int
    confidence: float
    factors: List[str]
    recommendation: str
    model_name: str
    model_version: str


# -------------------------------------------------------------
# 4. ROUTE RE-OPTIMIZATION SCHEMAS
# -------------------------------------------------------------
class RouteReoptimizationRequest(BaseModel):
    trigger_reason: Optional[str] = "Operator manual dynamic re-optimization request"


class RouteReoptimizationResponse(BaseModel):
    route_id: str
    reoptimization_required: bool
    reoptimization_beneficial: bool
    trigger_reason: Optional[str] = None
    reasons: List[str]
    original_distance_km: float
    optimized_distance_km: float
    estimated_distance_change_km: float
    estimated_time_saved_minutes: float
    estimated_fuel_saved_liters: float
    estimated_cost_saved: float
    new_proposed_route: Optional[Dict[str, Any]] = None
    recommendation: str
    model_name: str
    model_version: str


# -------------------------------------------------------------
# 5. OPERATIONS SUMMARY SCHEMA
# -------------------------------------------------------------
class OperationsSummaryResponse(BaseModel):
    critical_orders_count: int
    critical_orders: List[Dict[str, Any]]
    high_delay_risk_count: int
    high_delay_risk_orders: List[Dict[str, Any]]
    recommended_assignments_count: int
    recommended_assignments: List[Dict[str, Any]]
    routes_needing_reoptimization_count: int
    route_reoptimization_opportunities: List[Dict[str, Any]]
    estimated_fleet_time_saved_minutes: float
    estimated_fleet_distance_saved_km: float
    estimated_fleet_fuel_saved_liters: float
    estimated_fleet_cost_saved_usd: float
    demand_forecast_glance: Dict[str, Any]
    system_status: str
    timestamp: str
