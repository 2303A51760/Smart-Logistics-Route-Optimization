from typing import Optional
from datetime import datetime
import enum
from pydantic import BaseModel, Field, field_validator


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class VehicleBase(BaseModel):
    vehicle_number: str = Field(..., min_length=2, max_length=50, example="VH-893-TR")
    vehicle_type: str = Field(default="VAN", min_length=2, max_length=50, example="VAN")
    capacity: float = Field(..., gt=0, example=1200.0, description="Capacity must be greater than 0")
    fuel_type: str = Field(default="DIESEL", max_length=30, example="DIESEL")
    mileage: float = Field(default=0.0, ge=0, example=14500.0, description="Mileage cannot be negative")
    status: VehicleStatus = Field(default=VehicleStatus.AVAILABLE, example=VehicleStatus.AVAILABLE)
    driver_id: Optional[str] = None

    # Backward compatibility with Phase 1
    name: Optional[str] = None
    license_plate: Optional[str] = None


class VehicleCreate(BaseModel):
    vehicle_number: Optional[str] = None
    vehicle_type: str = Field(default="VAN", min_length=2, max_length=50)
    capacity: Optional[float] = None
    fuel_type: str = Field(default="DIESEL", max_length=30)
    mileage: float = Field(default=0.0, ge=0)
    status: VehicleStatus = Field(default=VehicleStatus.AVAILABLE)
    driver_id: Optional[str] = None

    # Backward compatibility fields
    name: Optional[str] = None
    license_plate: Optional[str] = None
    capacity_kg: Optional[float] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    fuel_level_percent: Optional[float] = None
    is_active: Optional[bool] = True

    @field_validator("capacity", mode="before")
    @classmethod
    def validate_capacity_value(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Capacity must be greater than 0")
        return v

    @field_validator("mileage", mode="before")
    @classmethod
    def validate_mileage_value(cls, v):
        if v is not None and v < 0:
            raise ValueError("Mileage cannot be negative")
        return v


class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = Field(None, min_length=2, max_length=50)
    vehicle_type: Optional[str] = Field(None, min_length=2, max_length=50)
    capacity: Optional[float] = Field(None, gt=0)
    fuel_type: Optional[str] = Field(None, max_length=30)
    mileage: Optional[float] = Field(None, ge=0)
    status: Optional[VehicleStatus] = None
    driver_id: Optional[str] = None
    name: Optional[str] = None
    license_plate: Optional[str] = None


class VehicleResponse(BaseModel):
    id: str
    vehicle_number: str
    vehicle_type: str
    capacity: float
    fuel_type: str
    mileage: float
    status: str
    driver_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Backward compatibility aliases
    name: str = ""
    license_plate: str = ""
    capacity_kg: float = 0.0
    current_lat: float = 40.7128
    current_lng: float = -74.0060
    fuel_level_percent: float = 100.0
    is_active: bool = True
    assigned_driver_name: Optional[str] = None

    class Config:
        from_attributes = True
