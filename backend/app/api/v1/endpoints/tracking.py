import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.driver import Driver
from app.models.location import DriverLocation
from app.core.logistics_store import (
    SEED_DRIVERS,
    get_driver_locations_from_store,
)
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
    if await check_db_connection():
        try:
            res = await db.execute(select(Driver).where(Driver.user_id == user.id))
            drv = res.scalar_one_or_none()
            if drv:
                return drv.id
        except Exception:
            pass

    for d_id, d_data in SEED_DRIVERS.items():
        if d_data.get("user_id") == user.id:
            return d_id
    if user.id in SEED_DRIVERS:
        return user.id
    # Default fallback for driver user
    if user.role == UserRole.DRIVER.value:
        return "drv-001"
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
        # Fetch driver from DB or seed
        if await check_db_connection():
            try:
                res = await db.execute(select(Driver).where(Driver.id == self_driver_id))
                drv = res.scalar_one_or_none()
                if drv:
                    drivers_list.append(
                        DriverLocationResponse(
                            driver_id=drv.id,
                            name=drv.user.name if drv.user else current_user.name,
                            latitude=drv.current_latitude or 40.7128,
                            longitude=drv.current_longitude or -74.0060,
                            status=drv.status,
                            last_updated=drv.updated_at,
                        )
                    )
                    return DriverLocationsListResponse(drivers=drivers_list)
            except Exception:
                pass

        # Seed fallback
        drv_data = SEED_DRIVERS.get(self_driver_id, {})
        drivers_list.append(
            DriverLocationResponse(
                driver_id=self_driver_id,
                name=current_user.name,
                latitude=drv_data.get("current_latitude", 40.7128),
                longitude=drv_data.get("current_longitude", -74.0060),
                status=drv_data.get("status", "AVAILABLE"),
                speed=drv_data.get("speed"),
                heading=drv_data.get("heading"),
                last_updated=drv_data.get("updated_at"),
            )
        )
        return DriverLocationsListResponse(drivers=drivers_list)

    # For ADMIN / LOGISTICS_MANAGER: Retrieve all operational drivers
    if await check_db_connection():
        try:
            res = await db.execute(select(Driver))
            db_drivers = res.scalars().all()
            if db_drivers:
                for drv in db_drivers:
                    drivers_list.append(
                        DriverLocationResponse(
                            driver_id=drv.id,
                            name=drv.user.name if drv.user else f"Driver {drv.id[-4:]}",
                            latitude=drv.current_latitude or 40.7128,
                            longitude=drv.current_longitude or -74.0060,
                            status=drv.status,
                            last_updated=drv.updated_at,
                        )
                    )
                return DriverLocationsListResponse(drivers=drivers_list)
        except Exception as e:
            logger.warning(f"Error reading drivers from DB: {e}")

    # Fallback to seed drivers
    for d_id, d_val in SEED_DRIVERS.items():
        drivers_list.append(
            DriverLocationResponse(
                driver_id=d_id,
                name=f"Driver {d_id}",
                latitude=d_val.get("current_latitude", 40.7128),
                longitude=d_val.get("current_longitude", -74.0060),
                status=d_val.get("status", "AVAILABLE"),
                speed=d_val.get("speed"),
                heading=d_val.get("heading"),
                last_updated=d_val.get("updated_at"),
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
    # Enforce driver isolation
    if current_user.role == UserRole.DRIVER.value:
        self_driver_id = await get_driver_id_for_user(current_user, db)
        if self_driver_id != driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Drivers are only authorized to access their own location history.",
            )

    history_items: List[LocationHistoryItem] = []

    # Query PostgreSQL if available
    if await check_db_connection():
        try:
            query = select(DriverLocation).where(DriverLocation.driver_id == driver_id)
            if start_time:
                query = query.where(DriverLocation.timestamp >= start_time)
            if end_time:
                query = query.where(DriverLocation.timestamp <= end_time)
            query = query.order_by(desc(DriverLocation.timestamp)).limit(limit)

            res = await db.execute(query)
            db_locations = res.scalars().all()
            for loc in db_locations:
                history_items.append(
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
                )
            return DriverLocationHistoryResponse(
                driver_id=driver_id,
                total_points=len(history_items),
                locations=history_items,
            )
        except Exception as e:
            logger.warning(f"Error querying location history from DB: {e}")

    # Fallback to in-memory store
    store_locations = get_driver_locations_from_store(
        driver_id=driver_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    for loc in store_locations:
        history_items.append(
            LocationHistoryItem(
                id=loc["id"],
                driver_id=loc["driver_id"],
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                accuracy=loc.get("accuracy"),
                speed=loc.get("speed"),
                heading=loc.get("heading"),
                timestamp=loc["timestamp"],
            )
        )

    return DriverLocationHistoryResponse(
        driver_id=driver_id,
        total_points=len(history_items),
        locations=history_items,
    )
