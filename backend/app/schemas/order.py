from typing import Optional, List
from datetime import datetime
import enum
from pydantic import BaseModel, Field, field_validator


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    ARRIVED = "ARRIVED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class OrderPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class OrderBase(BaseModel):
    order_number: str = Field(..., min_length=2, max_length=100, example="ORD-1092")
    customer_id: str = Field(..., example="cust-001")
    warehouse_id: str = Field(..., example="wh-001")
    pickup_latitude: float = Field(..., ge=-90.0, le=90.0, example=40.7357)
    pickup_longitude: float = Field(..., ge=-180.0, le=180.0, example=-74.1724)
    delivery_latitude: float = Field(..., ge=-90.0, le=90.0, example=40.7484)
    delivery_longitude: float = Field(..., ge=-180.0, le=180.0, example=-73.9857)
    package_weight: float = Field(..., gt=0, example=24.5, description="Package weight must be greater than 0")
    priority: OrderPriority = Field(default=OrderPriority.NORMAL, example=OrderPriority.NORMAL)
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    status: OrderStatus = Field(default=OrderStatus.PENDING, example=OrderStatus.PENDING)
    assigned_driver_id: Optional[str] = None


class OrderCreate(BaseModel):
    order_number: str = Field(..., min_length=2, max_length=100, example="ORD-1092")
    customer_id: str = Field(..., example="cust-001")
    warehouse_id: str = Field(..., example="wh-001")
    pickup_latitude: float = Field(..., ge=-90.0, le=90.0, example=40.7357)
    pickup_longitude: float = Field(..., ge=-180.0, le=180.0, example=-74.1724)
    delivery_latitude: float = Field(..., ge=-90.0, le=90.0, example=40.7484)
    delivery_longitude: float = Field(..., ge=-180.0, le=180.0, example=-73.9857)
    package_weight: float = Field(..., gt=0, example=24.5)
    priority: OrderPriority = Field(default=OrderPriority.NORMAL)
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    assigned_driver_id: Optional[str] = None

    @field_validator("package_weight")
    @classmethod
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError("Package weight must be greater than 0")
        return v


class OrderUpdate(BaseModel):
    order_number: Optional[str] = Field(None, min_length=2, max_length=100)
    customer_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    pickup_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    pickup_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    delivery_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    delivery_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    package_weight: Optional[float] = Field(None, gt=0)
    priority: Optional[OrderPriority] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    status: Optional[OrderStatus] = None
    assigned_driver_id: Optional[str] = None


class OrderResponse(OrderBase):
    id: str
    created_at: datetime
    updated_at: datetime
    customer_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    assigned_driver_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    size: int
    total_pages: int
