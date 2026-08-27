import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user, require_manager
from app.models.user import User, UserRole
from app.models.driver import Driver, DriverStatus
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from app.core.logistics_store import SEED_DRIVERS, SEED_VEHICLES
from app.core.seed import SEED_USERS

router = APIRouter()


def _format_driver_dict(d: dict) -> dict:
    # Lookup user name and assigned vehicle
    user_name = None
    if d.get("user_id"):
        for u in SEED_USERS.values():
            if u["id"] == d["user_id"]:
                user_name = u["name"]
                break

    assigned_v = None
    for v in SEED_VEHICLES.values():
        if v.get("driver_id") == d["id"]:
            assigned_v = v.get("vehicle_number")
            break

    return {
        **d,
        "user_name": user_name,
        "assigned_vehicle_number": assigned_v,
    }


@router.get("", response_model=List[DriverResponse])
async def list_drivers(
    status: Optional[DriverStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List drivers. Managers/Admins see all; Drivers only see their own profile."""
    # If user is Driver, only return their own driver profile
    if current_user.role == UserRole.DRIVER.value:
        my_drivers = [
            _format_driver_dict(d)
            for d in SEED_DRIVERS.values()
            if d.get("user_id") == current_user.id
        ]
        return my_drivers

    # If DB is connected
    if await check_db_connection():
        try:
            stmt = select(Driver)
            if status:
                stmt = stmt.where(Driver.status == status.value)
            result = await db.execute(stmt)
            db_drivers = result.scalars().all()
            if db_drivers:
                return db_drivers
        except Exception:
            pass

    # In-memory store
    drivers = list(SEED_DRIVERS.values())
    if status:
        drivers = [d for d in drivers if d.get("status") == status.value]
    return [_format_driver_dict(d) for d in drivers]


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_in: DriverCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new driver (Admin/Manager only)."""
    # Check unique license
    for d in SEED_DRIVERS.values():
        if d["license_number"] == driver_in.license_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver with license number '{driver_in.license_number}' already exists",
            )

    driver_id = f"drv-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_driver = {
        "id": driver_id,
        "license_number": driver_in.license_number,
        "phone": driver_in.phone,
        "status": driver_in.status.value,
        "current_latitude": driver_in.current_latitude or 40.7128,
        "current_longitude": driver_in.current_longitude or -74.0060,
        "user_id": driver_in.user_id,
        "created_at": now,
        "updated_at": now,
    }

    if await check_db_connection():
        try:
            db_driver = Driver(**new_driver)
            db.add(db_driver)
            await db.commit()
            await db.refresh(db_driver)
        except Exception:
            pass

    SEED_DRIVERS[driver_id] = new_driver
    return _format_driver_dict(new_driver)


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single driver details."""
    driver_dict = SEED_DRIVERS.get(driver_id)
    if not driver_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # If Driver role, verify authorization to access own profile
    if current_user.role == UserRole.DRIVER.value and driver_dict.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only authorized to access your own driver profile",
        )

    return _format_driver_dict(driver_dict)


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_in: DriverUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update driver details."""
    driver_dict = SEED_DRIVERS.get(driver_id)
    if not driver_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Driver role can only update their own status/location
    if current_user.role == UserRole.DRIVER.value:
        if driver_dict.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own driver profile",
            )
        # Drivers can update status and location
        if driver_in.status:
            driver_dict["status"] = driver_in.status.value
        if driver_in.current_latitude is not None:
            driver_dict["current_latitude"] = driver_in.current_latitude
        if driver_in.current_longitude is not None:
            driver_dict["current_longitude"] = driver_in.current_longitude
        if driver_in.phone:
            driver_dict["phone"] = driver_in.phone
    else:
        # Admin / Manager full update
        if driver_in.license_number:
            # Check uniqueness if changed
            for did, d in SEED_DRIVERS.items():
                if did != driver_id and d["license_number"] == driver_in.license_number:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Driver with this license number already exists",
                    )
            driver_dict["license_number"] = driver_in.license_number

        if driver_in.phone:
            driver_dict["phone"] = driver_in.phone
        if driver_in.status:
            driver_dict["status"] = driver_in.status.value
        if driver_in.current_latitude is not None:
            driver_dict["current_latitude"] = driver_in.current_latitude
        if driver_in.current_longitude is not None:
            driver_dict["current_longitude"] = driver_in.current_longitude
        if driver_in.user_id is not None:
            driver_dict["user_id"] = driver_in.user_id

    driver_dict["updated_at"] = datetime.utcnow()
    SEED_DRIVERS[driver_id] = driver_dict

    return _format_driver_dict(driver_dict)


@router.delete("/{driver_id}", status_code=status.HTTP_200_OK)
async def delete_driver(
    driver_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete a driver (Admin/Manager only)."""
    if driver_id not in SEED_DRIVERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Unassign any vehicles
    for v in SEED_VEHICLES.values():
        if v.get("driver_id") == driver_id:
            v["driver_id"] = None
            v["status"] = "AVAILABLE"

    del SEED_DRIVERS[driver_id]
    return {"status": "success", "message": f"Driver {driver_id} deleted successfully"}
