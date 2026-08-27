from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ForecastItem(BaseModel):
    date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    predicted_orders: int = Field(..., description="Predicted number of delivery orders")
    lower_bound: Optional[int] = Field(None, description="Lower prediction interval bound (~95% confidence)")
    upper_bound: Optional[int] = Field(None, description="Upper prediction interval bound (~95% confidence)")


class DemandForecastResponse(BaseModel):
    forecast: List[ForecastItem]
    model_version: str = "demand-v1"
    selected_model: Optional[str] = "RandomForestRegressor"
    source: str = "ML"  # "ML" or "FALLBACK"
    reason: Optional[str] = None
    horizon_days: int = 7
    warehouse_id: Optional[str] = None


class CapacityPlanningResponse(BaseModel):
    horizon_days: int
    forecasted_total_demand: int
    daily_average_demand: float
    peak_daily_demand: int
    available_capacity: int
    capacity_utilization_percent: float
    capacity_gap: int
    status: str  # "UNDER_UTILIZED", "NORMAL", "HIGH_UTILIZATION", "OVER_CAPACITY"
    active_drivers: int
    active_vehicles: int
    required_drivers: int
    required_vehicles: int
    warehouse_capacity_kg: Optional[float] = None
    assumptions: Dict[str, Any]


class WarehouseCapacityComparisonItem(BaseModel):
    warehouse_id: str
    warehouse_name: str
    forecasted_demand: int
    capacity: int
    utilization_percent: float
    status: str


class WarehouseComparisonResponse(BaseModel):
    horizon_days: int
    warehouses: List[WarehouseCapacityComparisonItem]


class DemandAnalyticsResponse(BaseModel):
    model_version: str
    selected_model: str
    trained_at: Optional[str] = None
    training_samples: int
    features: List[str]
    selected_metrics: Dict[str, float]
    models_evaluated: Optional[Dict[str, Any]] = None
    status: Optional[str] = "READY"
