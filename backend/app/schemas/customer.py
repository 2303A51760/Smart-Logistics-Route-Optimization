from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, example="Acme Corporation")
    phone: str = Field(..., min_length=5, max_length=30, example="+1-212-555-0199")
    email: EmailStr = Field(..., example="orders@acme.com")
    address: str = Field(..., min_length=3, max_length=255, example="350 5th Ave, New York, NY")
    latitude: float = Field(..., ge=-90.0, le=90.0, example=40.7484, description="Latitude must be between -90 and 90")
    longitude: float = Field(..., ge=-180.0, le=180.0, example=-73.9857, description="Longitude must be between -180 and 180")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = Field(None, min_length=5, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, min_length=3, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class CustomerResponse(CustomerBase):
    id: str
    created_at: datetime
    updated_at: datetime
    total_orders_count: Optional[int] = 0

    class Config:
        from_attributes = True
