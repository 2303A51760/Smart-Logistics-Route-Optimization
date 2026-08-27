from typing import List, Optional
from pydantic import BaseModel, field_validator


class MapDriverItem(BaseModel):
    id: str
    name: str
    license_number: str
    phone: str
    status: str
    latitude: float
    longitude: float
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class MapWarehouseItem(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    capacity: float

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class MapOrderItem(BaseModel):
    id: str
    order_number: str
    customer_name: str
    delivery_address: Optional[str] = None
    pickup_latitude: float
    pickup_longitude: float
    delivery_latitude: float
    delivery_longitude: float
    priority: str
    status: str
    package_weight: float
    assigned_driver_id: Optional[str] = None
    assigned_driver_name: Optional[str] = None

    @field_validator("pickup_latitude", "delivery_latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("pickup_longitude", "delivery_longitude")
    @classmethod
    def validate_lng(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class MapOverviewResponse(BaseModel):
    drivers: List[MapDriverItem]
    warehouses: List[MapWarehouseItem]
    orders: List[MapOrderItem]
