import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user, require_manager
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.core.logistics_store import SEED_WAREHOUSES, SEED_ORDERS

router = APIRouter()


def _format_warehouse(wh: dict) -> dict:
    orders_count = sum(1 for o in SEED_ORDERS.values() if o.get("warehouse_id") == wh["id"])
    return {
        **wh,
        "active_orders_count": orders_count,
    }


@router.get("", response_model=List[WarehouseResponse])
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
):
    """List all warehouses."""
    if await check_db_connection():
        try:
            result = await db.execute(select(Warehouse))
            db_wh = result.scalars().all()
            if db_wh:
                return [_format_warehouse(w.__dict__) for w in db_wh]
        except Exception:
            pass

    return [_format_warehouse(wh) for wh in SEED_WAREHOUSES.values()]


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    warehouse_in: WarehouseCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a new warehouse location (Admin/Manager only)."""
    if warehouse_in.capacity <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Capacity must be greater than 0",
        )

    if not (-90.0 <= warehouse_in.latitude <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Latitude must be between -90 and 90",
        )

    if not (-180.0 <= warehouse_in.longitude <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Longitude must be between -180 and 180",
        )

    new_id = f"wh-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_wh = {
        "id": new_id,
        "name": warehouse_in.name,
        "address": warehouse_in.address,
        "latitude": warehouse_in.latitude,
        "longitude": warehouse_in.longitude,
        "capacity": warehouse_in.capacity,
        "created_at": now,
        "updated_at": now,
    }

    if await check_db_connection():
        try:
            db_w = Warehouse(**new_wh)
            db.add(db_w)
            await db.commit()
            await db.refresh(db_w)
        except Exception:
            pass

    SEED_WAREHOUSES[new_id] = new_wh
    return _format_warehouse(new_wh)


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str, db: AsyncSession = Depends(get_db)):
    """Get warehouse details."""
    wh = SEED_WAREHOUSES.get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return _format_warehouse(wh)


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    warehouse_in: WarehouseUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update warehouse details (Admin/Manager only)."""
    wh = SEED_WAREHOUSES.get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    if warehouse_in.capacity is not None:
        if warehouse_in.capacity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Capacity must be greater than 0",
            )
        wh["capacity"] = warehouse_in.capacity

    if warehouse_in.latitude is not None:
        if not (-90.0 <= warehouse_in.latitude <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude must be between -90 and 90",
            )
        wh["latitude"] = warehouse_in.latitude

    if warehouse_in.longitude is not None:
        if not (-180.0 <= warehouse_in.longitude <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Longitude must be between -180 and 180",
            )
        wh["longitude"] = warehouse_in.longitude

    if warehouse_in.name:
        wh["name"] = warehouse_in.name
    if warehouse_in.address:
        wh["address"] = warehouse_in.address

    wh["updated_at"] = datetime.utcnow()
    SEED_WAREHOUSES[warehouse_id] = wh
    return _format_warehouse(wh)


@router.delete("/{warehouse_id}", status_code=status.HTTP_200_OK)
async def delete_warehouse(
    warehouse_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete warehouse (Admin/Manager only)."""
    if warehouse_id not in SEED_WAREHOUSES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    del SEED_WAREHOUSES[warehouse_id]
    return {"status": "success", "message": f"Warehouse {warehouse_id} deleted successfully"}
