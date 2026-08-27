import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, check_db_connection
from app.api.deps import get_current_user, require_manager
from app.models.user import User
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.logistics_store import SEED_CUSTOMERS, SEED_ORDERS

router = APIRouter()


def _format_customer(c: dict) -> dict:
    orders_count = sum(1 for o in SEED_ORDERS.values() if o.get("customer_id") == c["id"])
    return {
        **c,
        "total_orders_count": orders_count,
    }


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    db: AsyncSession = Depends(get_db),
):
    """List all customers."""
    if await check_db_connection():
        try:
            result = await db.execute(select(Customer))
            db_cust = result.scalars().all()
            if db_cust:
                return [_format_customer(c.__dict__) for c in db_cust]
        except Exception:
            pass

    return [_format_customer(c) for c in SEED_CUSTOMERS.values()]


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a new customer profile (Admin/Manager only)."""
    if not (-90.0 <= customer_in.latitude <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Latitude must be between -90 and 90",
        )

    if not (-180.0 <= customer_in.longitude <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Longitude must be between -180 and 180",
        )

    new_id = f"cust-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()

    new_cust = {
        "id": new_id,
        "name": customer_in.name,
        "phone": customer_in.phone,
        "email": customer_in.email,
        "address": customer_in.address,
        "latitude": customer_in.latitude,
        "longitude": customer_in.longitude,
        "created_at": now,
        "updated_at": now,
    }

    if await check_db_connection():
        try:
            db_c = Customer(**new_cust)
            db.add(db_c)
            await db.commit()
            await db.refresh(db_c)
        except Exception:
            pass

    SEED_CUSTOMERS[new_id] = new_cust
    return _format_customer(new_cust)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get single customer details."""
    c = SEED_CUSTOMERS.get(customer_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return _format_customer(c)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_in: CustomerUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update customer details (Admin/Manager only)."""
    c = SEED_CUSTOMERS.get(customer_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if customer_in.latitude is not None:
        if not (-90.0 <= customer_in.latitude <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude must be between -90 and 90",
            )
        c["latitude"] = customer_in.latitude

    if customer_in.longitude is not None:
        if not (-180.0 <= customer_in.longitude <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Longitude must be between -180 and 180",
            )
        c["longitude"] = customer_in.longitude

    if customer_in.name:
        c["name"] = customer_in.name
    if customer_in.phone:
        c["phone"] = customer_in.phone
    if customer_in.email:
        c["email"] = customer_in.email
    if customer_in.address:
        c["address"] = customer_in.address

    c["updated_at"] = datetime.utcnow()
    SEED_CUSTOMERS[customer_id] = c
    return _format_customer(c)


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete a customer record (Admin/Manager only)."""
    if customer_id not in SEED_CUSTOMERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    del SEED_CUSTOMERS[customer_id]
    return {"status": "success", "message": f"Customer {customer_id} deleted successfully"}
