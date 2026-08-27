from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.maintenance import MaintenanceType, MaintenanceStatus


class MaintenanceBase(BaseModel):
    vehicle_id: str
    maintenance_type: MaintenanceType = MaintenanceType.GENERAL_INSPECTION
    maintenance_date: Optional[datetime] = None
    mileage: float = Field(ge=0.0, description="Odometer mileage at time of maintenance")
    notes: Optional[str] = None
    next_maintenance_mileage: float = Field(ge=0.0, description="Mileage when next maintenance is scheduled")
    cost: float = Field(default=0.0, ge=0.0, description="Cost of maintenance event")
    status: MaintenanceStatus = MaintenanceStatus.COMPLETED


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    maintenance_type: Optional[MaintenanceType] = None
    maintenance_date: Optional[datetime] = None
    mileage: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None
    next_maintenance_mileage: Optional[float] = Field(None, ge=0.0)
    cost: Optional[float] = Field(None, ge=0.0)
    status: Optional[MaintenanceStatus] = None


class MaintenanceResponse(MaintenanceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None

    class Config:
        from_attributes = True


class MaintenanceListResponse(BaseModel):
    items: List[MaintenanceResponse]
    total: int


class MaintenanceVehicleDue(BaseModel):
    vehicle_id: str
    vehicle_number: str
    vehicle_type: str
    current_mileage: float
    last_maintenance_date: Optional[datetime] = None
    last_maintenance_mileage: Optional[float] = None
    next_maintenance_mileage: float
    mileage_overdue: float
    is_overdue: bool
    status: str
    assigned_driver_id: Optional[str] = None
    assigned_driver_name: Optional[str] = None


class MaintenanceSummaryResponse(BaseModel):
    total_records: int
    completed_services: int
    scheduled_services: int
    total_maintenance_cost: float
    vehicles_overdue_count: int
    vehicles_due_soon_count: int
    fleet_health_score: float
    by_type: dict
