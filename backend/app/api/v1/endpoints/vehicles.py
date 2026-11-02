import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import require_manager
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse

router = APIRouter()


def _format_vehicle(v: Vehicle, driver_license: Optional[str] = None) -> VehicleResponse:
    assigned_name = f"Driver {driver_license}" if driver_license else None
    v_num = v.vehicle_number
    v_type = v.vehicle_type
    v_cap = float(v.capacity)
    return VehicleResponse(
        id=v.id,
        vehicle_number=v_num,
        vehicle_type=v_type,
        capacity=v_cap,
        fuel_type=v.fuel_type,
        mileage=float(v.mileage or 0.0),
        status=v.status,
        driver_id=v.driver_id,
        created_at=v.created_at,
        updated_at=v.updated_at,
        name=f"Fleet {v_type.capitalize()} ({v_num})",
        license_plate=v_num,
        capacity_kg=v_cap,
        current_lat=40.7128,
        current_lng=-74.0060,
        fuel_level_percent=85.0,
        is_active=True,
        assigned_driver_name=assigned_name,
    )


@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all vehicles in the fleet."""
    stmt = select(Vehicle)
    if status:
        stmt = stmt.where(Vehicle.status == status)

    result = await db.execute(stmt.order_by(Vehicle.created_at))
    vehicles = result.scalars().all()

    driver_ids = [v.driver_id for v in vehicles if v.driver_id]
    drivers_map = {}
    if driver_ids:
        d_res = await db.execute(select(Driver.id, Driver.license_number).where(Driver.id.in_(driver_ids)))
        drivers_map = dict(d_res.all())

    return [_format_vehicle(v, drivers_map.get(v.driver_id)) for v in vehicles]


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_in: VehicleCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new vehicle into the fleet (Admin/Manager only)."""
    v_num = vehicle_in.vehicle_number or vehicle_in.license_plate
    if not v_num:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vehicle number is required",
        )

    cap = vehicle_in.capacity if vehicle_in.capacity is not None else vehicle_in.capacity_kg
    if cap is None or cap <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Capacity must be greater than 0",
        )

    if vehicle_in.mileage < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mileage cannot be negative",
        )

    # Check vehicle number uniqueness
    existing = await db.execute(select(Vehicle).where(Vehicle.vehicle_number == v_num))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle with number '{v_num}' already exists",
        )

    driver_license = None
    if vehicle_in.driver_id:
        d_res = await db.execute(select(Driver).where(Driver.id == vehicle_in.driver_id))
        driver = d_res.scalar_one_or_none()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver '{vehicle_in.driver_id}' does not exist",
            )
        driver_license = driver.license_number

    new_id = f"veh-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()
    status_val = vehicle_in.status.value if hasattr(vehicle_in.status, "value") else str(vehicle_in.status)

    new_vehicle = Vehicle(
        id=new_id,
        vehicle_number=v_num,
        vehicle_type=vehicle_in.vehicle_type,
        capacity=cap,
        fuel_type=vehicle_in.fuel_type,
        mileage=vehicle_in.mileage,
        status=status_val,
        driver_id=vehicle_in.driver_id,
        created_at=now,
        updated_at=now,
    )
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)

    return _format_vehicle(new_vehicle, driver_license)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Get single vehicle details."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    driver_license = None
    if v.driver_id:
        d_res = await db.execute(select(Driver.license_number).where(Driver.id == v.driver_id))
        driver_license = d_res.scalar_one_or_none()

    return _format_vehicle(v, driver_license)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    vehicle_in: VehicleUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update vehicle specifications or driver assignment (Admin/Manager only)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    v_num = vehicle_in.vehicle_number or vehicle_in.license_plate
    if v_num and v_num != v.vehicle_number:
        existing = await db.execute(select(Vehicle).where(Vehicle.vehicle_number == v_num, Vehicle.id != vehicle_id))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with number '{v_num}' already exists",
            )
        v.vehicle_number = v_num

    if vehicle_in.capacity is not None:
        if vehicle_in.capacity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Capacity must be greater than 0",
            )
        v.capacity = vehicle_in.capacity

    if vehicle_in.mileage is not None:
        if vehicle_in.mileage < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mileage cannot be negative",
            )
        v.mileage = vehicle_in.mileage

    driver_license = None
    if vehicle_in.driver_id is not None:
        if vehicle_in.driver_id:
            d_res = await db.execute(select(Driver).where(Driver.id == vehicle_in.driver_id))
            driver = d_res.scalar_one_or_none()
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver '{vehicle_in.driver_id}' does not exist",
                )
            driver_license = driver.license_number
        v.driver_id = vehicle_in.driver_id
    elif v.driver_id:
        d_res = await db.execute(select(Driver.license_number).where(Driver.id == v.driver_id))
        driver_license = d_res.scalar_one_or_none()

    if vehicle_in.vehicle_type:
        v.vehicle_type = vehicle_in.vehicle_type
    if vehicle_in.fuel_type:
        v.fuel_type = vehicle_in.fuel_type
    if vehicle_in.status:
        v.status = vehicle_in.status.value if hasattr(vehicle_in.status, "value") else str(vehicle_in.status)

    v.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(v)

    return _format_vehicle(v, driver_license)


@router.delete("/{vehicle_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle(
    vehicle_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vehicle from the fleet (Admin/Manager only)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    await db.delete(v)
    await db.commit()
    return {"status": "success", "message": f"Vehicle {vehicle_id} deleted successfully"}
