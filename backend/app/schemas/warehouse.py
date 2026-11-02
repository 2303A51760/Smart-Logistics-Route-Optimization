from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WarehouseBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, example="Central Hub Warehouse")
    address: str = Field(..., min_length=3, max_length=255, example="100 Logistics Blvd, Newark, NJ")
    latitude: float = Field(..., ge=-90.0, le=90.0, example=40.7357, description="Latitude must be between -90 and 90")
    longitude: float = Field(..., ge=-180.0, le=180.0, example=-74.1724, description="Longitude must be between -180 and 180")
    capacity: float = Field(..., gt=0, example=15000.0, description="Capacity must be greater than 0")


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    address: Optional[str] = Field(None, min_length=3, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    capacity: Optional[float] = Field(None, gt=0)


class WarehouseResponse(WarehouseBase):
    id: str
    created_at: datetime
    updated_at: datetime
    active_orders_count: Optional[int] = 0

    class Config:
        from_attributes = True
