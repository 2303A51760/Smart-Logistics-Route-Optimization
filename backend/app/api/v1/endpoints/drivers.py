import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.api.deps import get_current_user, require_manager
from app.models.user import User, UserRole
from app.models.driver import Driver, DriverStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter()


async def ensure_driver_profile(
    user_id: str,
    user_name: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> dict:
    """
    Ensures that a user with role DRIVER has a corresponding Driver profile.
    If a Driver profile already exists (by user_id), returns it.
    Otherwise, creates and links a new Driver record with valid default schema values.
    """
    if db is None:
        return {}

    stmt = select(Driver).where(Driver.user_id == user_id)
    result = await db.execute(stmt)
    db_driver = result.scalar_one_or_none()
    if db_driver:
        return {
            "id": db_driver.id,
            "user_id": db_driver.user_id,
            "license_number": db_driver.license_number,
            "phone": db_driver.phone,
            "status": db_driver.status,
            "current_latitude": db_driver.current_latitude or 40.7128,
            "current_longitude": db_driver.current_longitude or -74.0060,
            "created_at": db_driver.created_at or datetime.utcnow(),
            "updated_at": db_driver.updated_at or datetime.utcnow(),
        }

    unique_suffix = uuid.uuid4().hex[:6].upper()
    license_number = f"DL-NY-{unique_suffix}"
    driver_id = f"drv-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_driver = Driver(
        id=driver_id,
        user_id=user_id,
        license_number=license_number,
        phone="+1-555-0199",
        status=DriverStatus.AVAILABLE.value,
        current_latitude=40.7128,
        current_longitude=-74.0060,
        created_at=now,
        updated_at=now,
    )
    db.add(new_driver)
    await db.commit()
    await db.refresh(new_driver)

    return {
        "id": new_driver.id,
        "user_id": new_driver.user_id,
        "license_number": new_driver.license_number,
        "phone": new_driver.phone,
        "status": new_driver.status,
        "current_latitude": new_driver.current_latitude,
        "current_longitude": new_driver.current_longitude,
        "created_at": new_driver.created_at,
        "updated_at": new_driver.updated_at,
    }


@router.get("", response_model=List[DriverResponse])
async def list_drivers(
    status: Optional[DriverStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List drivers. Managers/Admins see all; Drivers only see their own profile."""
    stmt = select(Driver)
    if current_user.role == UserRole.DRIVER.value:
        stmt = stmt.where(Driver.user_id == current_user.id)
    elif status:
        stmt = stmt.where(Driver.status == status.value)

    result = await db.execute(stmt.order_by(Driver.created_at))
    drivers = result.scalars().all()

    user_ids = [d.user_id for d in drivers if d.user_id]
    driver_ids = [d.id for d in drivers]

    users_map = {}
    if user_ids:
        u_res = await db.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
        users_map = dict(u_res.all())

    vehicles_map = {}
    if driver_ids:
        v_res = await db.execute(
            select(Vehicle.driver_id, Vehicle.vehicle_number).where(Vehicle.driver_id.in_(driver_ids))
        )
        vehicles_map = dict(v_res.all())

    return [
        DriverResponse(
            id=d.id,
            user_id=d.user_id,
            license_number=d.license_number,
            phone=d.phone,
            status=d.status,
            current_latitude=d.current_latitude,
            current_longitude=d.current_longitude,
            created_at=d.created_at,
            updated_at=d.updated_at,
            user_name=users_map.get(d.user_id),
            assigned_vehicle_number=vehicles_map.get(d.id),
        )
        for d in drivers
    ]


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_in: DriverCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new driver (Admin/Manager only)."""
    existing = await db.execute(select(Driver).where(Driver.license_number == driver_in.license_number))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver with license number '{driver_in.license_number}' already exists",
        )

    driver_id = f"drv-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_driver = Driver(
        id=driver_id,
        license_number=driver_in.license_number,
        phone=driver_in.phone,
        status=driver_in.status.value if hasattr(driver_in.status, "value") else driver_in.status,
        current_latitude=driver_in.current_latitude or 40.7128,
        current_longitude=driver_in.current_longitude or -74.0060,
        user_id=driver_in.user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(new_driver)
    await db.commit()
    await db.refresh(new_driver)

    user_name = None
    if new_driver.user_id:
        u_res = await db.execute(select(User.name).where(User.id == new_driver.user_id))
        user_name = u_res.scalar_one_or_none()

    return DriverResponse(
        id=new_driver.id,
        user_id=new_driver.user_id,
        license_number=new_driver.license_number,
        phone=new_driver.phone,
        status=new_driver.status,
        current_latitude=new_driver.current_latitude,
        current_longitude=new_driver.current_longitude,
        created_at=new_driver.created_at,
        updated_at=new_driver.updated_at,
        user_name=user_name,
        assigned_vehicle_number=None,
    )


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single driver details."""
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    if current_user.role == UserRole.DRIVER.value and d.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only authorized to access your own driver profile",
        )

    user_name = None
    if d.user_id:
        u_res = await db.execute(select(User.name).where(User.id == d.user_id))
        user_name = u_res.scalar_one_or_none()

    v_res = await db.execute(select(Vehicle.vehicle_number).where(Vehicle.driver_id == d.id))
    assigned_vehicle = v_res.scalar_one_or_none()

    return DriverResponse(
        id=d.id,
        user_id=d.user_id,
        license_number=d.license_number,
        phone=d.phone,
        status=d.status,
        current_latitude=d.current_latitude,
        current_longitude=d.current_longitude,
        created_at=d.created_at,
        updated_at=d.updated_at,
        user_name=user_name,
        assigned_vehicle_number=assigned_vehicle,
    )


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_in: DriverUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update driver details."""
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    if current_user.role == UserRole.DRIVER.value:
        if d.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own driver profile",
            )
        if driver_in.status:
            d.status = driver_in.status.value if hasattr(driver_in.status, "value") else driver_in.status
        if driver_in.current_latitude is not None:
            d.current_latitude = driver_in.current_latitude
        if driver_in.current_longitude is not None:
            d.current_longitude = driver_in.current_longitude
        if driver_in.phone:
            d.phone = driver_in.phone
    else:
        if driver_in.license_number and driver_in.license_number != d.license_number:
            existing = await db.execute(
                select(Driver).where(Driver.license_number == driver_in.license_number, Driver.id != driver_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Driver with this license number already exists",
                )
            d.license_number = driver_in.license_number

        if driver_in.phone:
            d.phone = driver_in.phone
        if driver_in.status:
            d.status = driver_in.status.value if hasattr(driver_in.status, "value") else driver_in.status
        if driver_in.current_latitude is not None:
            d.current_latitude = driver_in.current_latitude
        if driver_in.current_longitude is not None:
            d.current_longitude = driver_in.current_longitude
        if driver_in.user_id is not None:
            d.user_id = driver_in.user_id

    d.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(d)

    user_name = None
    if d.user_id:
        u_res = await db.execute(select(User.name).where(User.id == d.user_id))
        user_name = u_res.scalar_one_or_none()

    v_res = await db.execute(select(Vehicle.vehicle_number).where(Vehicle.driver_id == d.id))
    assigned_vehicle = v_res.scalar_one_or_none()

    return DriverResponse(
        id=d.id,
        user_id=d.user_id,
        license_number=d.license_number,
        phone=d.phone,
        status=d.status,
        current_latitude=d.current_latitude,
        current_longitude=d.current_longitude,
        created_at=d.created_at,
        updated_at=d.updated_at,
        user_name=user_name,
        assigned_vehicle_number=assigned_vehicle,
    )


@router.delete("/{driver_id}", status_code=status.HTTP_200_OK)
async def delete_driver(
    driver_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete a driver (Admin/Manager only)."""
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Unassign any vehicles
    await db.execute(
        update(Vehicle).where(Vehicle.driver_id == driver_id).values(
            driver_id=None,
            status=VehicleStatus.AVAILABLE.value if hasattr(VehicleStatus.AVAILABLE, "value") else VehicleStatus.AVAILABLE
        )
    )

    await db.delete(d)
    await db.commit()
    return {"status": "success", "message": f"Driver {driver_id} deleted successfully"}
