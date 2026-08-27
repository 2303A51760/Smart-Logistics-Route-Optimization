from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LocationUpdateMessage(BaseModel):
    type: str = "location_update"
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180")
    accuracy: Optional[float] = Field(None, ge=0.0, description="Accuracy in meters >= 0")
    speed: Optional[float] = Field(None, ge=0.0, description="Speed in km/h >= 0")
    heading: Optional[float] = Field(None, ge=0.0, le=360.0, description="Heading in degrees 0-360")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v < -90.0 or v > 90.0:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v < -180.0 or v > 180.0:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class DriverLocationEvent(BaseModel):
    type: str = "driver_location_updated"
    driver_id: str
    driver_name: Optional[str] = None
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    status: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DriverLocationResponse(BaseModel):
    driver_id: str
    name: Optional[str] = None
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    status: Optional[str] = "AVAILABLE"
    last_updated: Optional[datetime] = None


class DriverLocationsListResponse(BaseModel):
    drivers: List[DriverLocationResponse]


class LocationHistoryItem(BaseModel):
    id: str
    driver_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime


class DriverLocationHistoryResponse(BaseModel):
    driver_id: str
    total_points: int
    locations: List[LocationHistoryItem]
