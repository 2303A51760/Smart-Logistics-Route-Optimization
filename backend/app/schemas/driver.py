from typing import Optional
from datetime import datetime
import enum
from pydantic import BaseModel, Field


class DriverStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    OFF_DUTY = "OFF_DUTY"
    INACTIVE = "INACTIVE"


class DriverBase(BaseModel):
    license_number: str = Field(..., min_length=3, max_length=50, example="DL-NY-98234")
    phone: str = Field(..., min_length=5, max_length=30, example="+1-555-0192")
    status: DriverStatus = Field(default=DriverStatus.AVAILABLE, example=DriverStatus.AVAILABLE)
    current_latitude: Optional[float] = Field(default=40.7128, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(default=-74.0060, ge=-180.0, le=180.0)
    user_id: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    license_number: Optional[str] = Field(None, min_length=3, max_length=50)
    phone: Optional[str] = Field(None, min_length=5, max_length=30)
    status: Optional[DriverStatus] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    user_id: Optional[str] = None


class DriverResponse(DriverBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    assigned_vehicle_number: Optional[str] = None

    class Config:
        from_attributes = True
