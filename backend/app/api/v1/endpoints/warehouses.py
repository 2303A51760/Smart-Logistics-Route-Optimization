import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import require_manager
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.order import Order
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse

router = APIRouter()


async def _get_warehouse_with_orders_count(wh: Warehouse, db: AsyncSession) -> WarehouseResponse:
    count_res = await db.execute(select(func.count(Order.id)).where(Order.warehouse_id == wh.id))
    orders_count = count_res.scalar() or 0
    return WarehouseResponse(
        id=wh.id,
        name=wh.name,
        address=wh.address,
        latitude=wh.latitude,
        longitude=wh.longitude,
        capacity=wh.capacity,
        created_at=wh.created_at,
        updated_at=wh.updated_at,
        active_orders_count=orders_count,
    )


@router.get("", response_model=List[WarehouseResponse])
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
):
    """List all warehouses."""
    result = await db.execute(select(Warehouse).order_by(Warehouse.name))
    warehouses = result.scalars().all()

    counts_res = await db.execute(select(Order.warehouse_id, func.count(Order.id)).group_by(Order.warehouse_id))
    counts_map = dict(counts_res.all())

    return [
        WarehouseResponse(
            id=wh.id,
            name=wh.name,
            address=wh.address,
            latitude=wh.latitude,
            longitude=wh.longitude,
            capacity=wh.capacity,
            created_at=wh.created_at,
            updated_at=wh.updated_at,
            active_orders_count=counts_map.get(wh.id, 0),
        )
        for wh in warehouses
    ]


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

    new_wh = Warehouse(
        id=new_id,
        name=warehouse_in.name,
        address=warehouse_in.address,
        latitude=warehouse_in.latitude,
        longitude=warehouse_in.longitude,
        capacity=warehouse_in.capacity,
        created_at=now,
        updated_at=now,
    )
    db.add(new_wh)
    await db.commit()
    await db.refresh(new_wh)

    return WarehouseResponse(
        id=new_wh.id,
        name=new_wh.name,
        address=new_wh.address,
        latitude=new_wh.latitude,
        longitude=new_wh.longitude,
        capacity=new_wh.capacity,
        created_at=new_wh.created_at,
        updated_at=new_wh.updated_at,
        active_orders_count=0,
    )


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str, db: AsyncSession = Depends(get_db)):
    """Get warehouse details."""
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    return await _get_warehouse_with_orders_count(wh, db)


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    warehouse_in: WarehouseUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update warehouse details (Admin/Manager only)."""
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    if warehouse_in.capacity is not None:
        if warehouse_in.capacity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Capacity must be greater than 0",
            )
        wh.capacity = warehouse_in.capacity

    if warehouse_in.latitude is not None:
        if not (-90.0 <= warehouse_in.latitude <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude must be between -90 and 90",
            )
        wh.latitude = warehouse_in.latitude

    if warehouse_in.longitude is not None:
        if not (-180.0 <= warehouse_in.longitude <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Longitude must be between -180 and 180",
            )
        wh.longitude = warehouse_in.longitude

    if warehouse_in.name is not None:
        wh.name = warehouse_in.name
    if warehouse_in.address is not None:
        wh.address = warehouse_in.address

    wh.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(wh)

    return await _get_warehouse_with_orders_count(wh, db)


@router.delete("/{warehouse_id}", status_code=status.HTTP_200_OK)
async def delete_warehouse(
    warehouse_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete warehouse (Admin/Manager only)."""
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    await db.delete(wh)
    await db.commit()
    return {"status": "success", "message": f"Warehouse {warehouse_id} deleted successfully"}
