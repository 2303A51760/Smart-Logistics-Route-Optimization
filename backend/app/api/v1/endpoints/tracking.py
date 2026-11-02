import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.driver import Driver
from app.models.location import DriverLocation
from app.schemas.tracking import (
    DriverLocationsListResponse,
    DriverLocationResponse,
    DriverLocationHistoryResponse,
    LocationHistoryItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_driver_id_for_user(user: User, db: AsyncSession) -> Optional[str]:
    """Helper to resolve driver ID for current user."""
    res = await db.execute(select(Driver.id).where(Driver.user_id == user.id))
    drv_id = res.scalar_one_or_none()
    if drv_id:
        return drv_id
    if user.role == UserRole.DRIVER.value:
        res_first = await db.execute(select(Driver.id).order_by(Driver.created_at))
        return res_first.scalar_one_or_none() or "drv-001"
    return None


@router.get("/drivers", response_model=DriverLocationsListResponse)
async def get_latest_driver_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get currently known operational driver locations.
    - ADMIN / LOGISTICS_MANAGER: Can view all operational drivers.
    - DRIVER: Can only retrieve their own location.
    """
    drivers_list: List[DriverLocationResponse] = []

    # If DRIVER role, filter only self
    if current_user.role == UserRole.DRIVER.value:
        self_driver_id = await get_driver_id_for_user(current_user, db)
        if not self_driver_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver profile not found for authenticated user",
            )
        res = await db.execute(select(Driver).where(Driver.id == self_driver_id))
        drv = res.scalar_one_or_none()
        if not drv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver profile not found for authenticated user",
            )

        user_name = current_user.name
        drivers_list.append(
            DriverLocationResponse(
                driver_id=drv.id,
                name=user_name,
                latitude=drv.current_latitude or 40.7128,
                longitude=drv.current_longitude or -74.0060,
                status=drv.status,
                last_updated=drv.updated_at,
            )
        )
        return DriverLocationsListResponse(drivers=drivers_list)

    # For ADMIN / LOGISTICS_MANAGER: Retrieve all operational drivers
    res = await db.execute(select(Driver).order_by(Driver.created_at))
    db_drivers = res.scalars().all()

    user_ids = [d.user_id for d in db_drivers if d.user_id]
    users_map = {}
    if user_ids:
        u_res = await db.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
        users_map = dict(u_res.all())

    for drv in db_drivers:
        name = users_map.get(drv.user_id, f"Driver {drv.id[-4:]}")
        drivers_list.append(
            DriverLocationResponse(
                driver_id=drv.id,
                name=name,
                latitude=drv.current_latitude or 40.7128,
                longitude=drv.current_longitude or -74.0060,
                status=drv.status,
                last_updated=drv.updated_at,
            )
        )

    return DriverLocationsListResponse(drivers=drivers_list)


@router.get("/drivers/{driver_id}/history", response_model=DriverLocationHistoryResponse)
async def get_driver_location_history(
    driver_id: str,
    start_time: Optional[datetime] = Query(None, description="Start timestamp filter (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End timestamp filter (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of history points (1-1000)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve location history for a specific driver.
    - Managers/Admins: Can inspect any permitted driver.
    - Driver: Can ONLY inspect their own history.
    """
    if current_user.role == UserRole.DRIVER.value:
        self_driver_id = await get_driver_id_for_user(current_user, db)
        if self_driver_id != driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Drivers are only authorized to access their own location history.",
            )

    query = select(DriverLocation).where(DriverLocation.driver_id == driver_id)
    if start_time:
        query = query.where(DriverLocation.timestamp >= start_time)
    if end_time:
        query = query.where(DriverLocation.timestamp <= end_time)
    query = query.order_by(desc(DriverLocation.timestamp)).limit(limit)

    res = await db.execute(query)
    db_locations = res.scalars().all()

    history_items = [
        LocationHistoryItem(
            id=loc.id,
            driver_id=loc.driver_id,
            latitude=loc.latitude,
            longitude=loc.longitude,
            accuracy=loc.accuracy,
            speed=loc.speed,
            heading=loc.heading,
            timestamp=loc.timestamp,
        )
        for loc in db_locations
    ]

    return DriverLocationHistoryResponse(
        driver_id=driver_id,
        total_points=len(history_items),
        locations=history_items,
    )
