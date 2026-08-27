import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user, require_manager
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.core.logistics_store import SEED_VEHICLES, SEED_DRIVERS

router = APIRouter()


def _format_vehicle_dict(v: dict) -> dict:
    assigned_name = None
    if v.get("driver_id") and v["driver_id"] in SEED_DRIVERS:
        driver = SEED_DRIVERS[v["driver_id"]]
        assigned_name = f"Driver {driver['license_number']}"

    v_num = v.get("vehicle_number") or v.get("license_plate") or "UNKNOWN"
    v_type = v.get("vehicle_type") or "VAN"
    v_cap = float(v.get("capacity") or v.get("capacity_kg") or 1000.0)
    v_mileage = float(v.get("mileage") or 0.0)
    v_fuel = v.get("fuel_type") or "DIESEL"
    v_status = v.get("status") or "AVAILABLE"

    return {
        "id": v["id"],
        "vehicle_number": v_num,
        "vehicle_type": v_type,
        "capacity": v_cap,
        "fuel_type": v_fuel,
        "mileage": v_mileage,
        "status": v_status,
        "driver_id": v.get("driver_id"),
        "created_at": v.get("created_at") or datetime.utcnow(),
        "updated_at": v.get("updated_at") or datetime.utcnow(),
        # Backwards compatibility fields
        "name": v.get("name") or f"Fleet {v_type.capitalize()} ({v_num})",
        "license_plate": v_num,
        "capacity_kg": v_cap,
        "current_lat": float(v.get("current_lat") or 40.7128),
        "current_lng": float(v.get("current_lng") or -74.0060),
        "fuel_level_percent": float(v.get("fuel_level_percent") or 85.0),
        "is_active": True,
        "assigned_driver_name": assigned_name,
    }


@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all vehicles in the fleet."""
    if await check_db_connection():
        try:
            result = await db.execute(select(Vehicle))
            vehicles = result.scalars().all()
            if vehicles:
                return [_format_vehicle_dict(v.__dict__) for v in vehicles]
        except Exception:
            pass

    vehicles = list(SEED_VEHICLES.values())
    if status:
        vehicles = [v for v in vehicles if v.get("status") == status]
    return [_format_vehicle_dict(v) for v in vehicles]


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_in: VehicleCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new vehicle into the fleet (Admin/Manager only)."""
    # Normalize vehicle number
    v_num = vehicle_in.vehicle_number or vehicle_in.license_plate
    if not v_num:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vehicle number is required",
        )

    # Validate capacity
    cap = vehicle_in.capacity if vehicle_in.capacity is not None else vehicle_in.capacity_kg
    if cap is None or cap <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Capacity must be greater than 0",
        )

    # Validate mileage
    if vehicle_in.mileage < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mileage cannot be negative",
        )

    # Check vehicle number uniqueness
    for v in SEED_VEHICLES.values():
        if v.get("vehicle_number") == v_num or v.get("license_plate") == v_num:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with number '{v_num}' already exists",
            )

    # Validate driver assignment if provided
    if vehicle_in.driver_id:
        if vehicle_in.driver_id not in SEED_DRIVERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver '{vehicle_in.driver_id}' does not exist",
            )

    new_id = f"veh-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_vehicle = {
        "id": new_id,
        "vehicle_number": v_num,
        "vehicle_type": vehicle_in.vehicle_type,
        "capacity": cap,
        "fuel_type": vehicle_in.fuel_type,
        "mileage": vehicle_in.mileage,
        "status": vehicle_in.status.value if hasattr(vehicle_in.status, "value") else str(vehicle_in.status),
        "driver_id": vehicle_in.driver_id,
        "created_at": now,
        "updated_at": now,
    }

    if await check_db_connection():
        try:
            db_v = Vehicle(**new_vehicle)
            db.add(db_v)
            await db.commit()
            await db.refresh(db_v)
        except Exception:
            pass

    SEED_VEHICLES[new_id] = new_vehicle
    return _format_vehicle_dict(new_vehicle)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Get single vehicle details."""
    v = SEED_VEHICLES.get(vehicle_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return _format_vehicle_dict(v)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    vehicle_in: VehicleUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update vehicle specifications or driver assignment (Admin/Manager only)."""
    v = SEED_VEHICLES.get(vehicle_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    v_num = vehicle_in.vehicle_number or vehicle_in.license_plate
    if v_num and v_num != v.get("vehicle_number"):
        for vid, other_v in SEED_VEHICLES.items():
            if vid != vehicle_id and other_v.get("vehicle_number") == v_num:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vehicle with number '{v_num}' already exists",
                )
        v["vehicle_number"] = v_num

    if vehicle_in.capacity is not None:
        if vehicle_in.capacity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Capacity must be greater than 0",
            )
        v["capacity"] = vehicle_in.capacity

    if vehicle_in.mileage is not None:
        if vehicle_in.mileage < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mileage cannot be negative",
            )
        v["mileage"] = vehicle_in.mileage

    if vehicle_in.driver_id is not None:
        if vehicle_in.driver_id and vehicle_in.driver_id not in SEED_DRIVERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver '{vehicle_in.driver_id}' does not exist",
            )
        v["driver_id"] = vehicle_in.driver_id

    if vehicle_in.vehicle_type:
        v["vehicle_type"] = vehicle_in.vehicle_type
    if vehicle_in.fuel_type:
        v["fuel_type"] = vehicle_in.fuel_type
    if vehicle_in.status:
        v["status"] = vehicle_in.status.value if hasattr(vehicle_in.status, "value") else str(vehicle_in.status)

    v["updated_at"] = datetime.utcnow()
    SEED_VEHICLES[vehicle_id] = v

    return _format_vehicle_dict(v)


@router.delete("/{vehicle_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle(
    vehicle_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vehicle from the fleet (Admin/Manager only)."""
    if vehicle_id not in SEED_VEHICLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    del SEED_VEHICLES[vehicle_id]
    return {"status": "success", "message": f"Vehicle {vehicle_id} deleted successfully"}
