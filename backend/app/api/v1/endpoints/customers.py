import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import require_manager
from app.models.user import User
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter()


async def _get_customer_with_orders_count(c: Customer, db: AsyncSession) -> CustomerResponse:
    count_res = await db.execute(select(func.count(Order.id)).where(Order.customer_id == c.id))
    orders_count = count_res.scalar() or 0
    return CustomerResponse(
        id=c.id,
        name=c.name,
        phone=c.phone,
        email=c.email,
        address=c.address,
        latitude=c.latitude,
        longitude=c.longitude,
        created_at=c.created_at,
        updated_at=c.updated_at,
        total_orders_count=orders_count,
    )


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    db: AsyncSession = Depends(get_db),
):
    """List all customers."""
    result = await db.execute(select(Customer).order_by(Customer.name))
    customers = result.scalars().all()

    counts_res = await db.execute(select(Order.customer_id, func.count(Order.id)).group_by(Order.customer_id))
    counts_map = dict(counts_res.all())

    return [
        CustomerResponse(
            id=c.id,
            name=c.name,
            phone=c.phone,
            email=c.email,
            address=c.address,
            latitude=c.latitude,
            longitude=c.longitude,
            created_at=c.created_at,
            updated_at=c.updated_at,
            total_orders_count=counts_map.get(c.id, 0),
        )
        for c in customers
    ]


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

    new_cust = Customer(
        id=new_id,
        name=customer_in.name,
        phone=customer_in.phone,
        email=customer_in.email,
        address=customer_in.address,
        latitude=customer_in.latitude,
        longitude=customer_in.longitude,
        created_at=now,
        updated_at=now,
    )
    db.add(new_cust)
    await db.commit()
    await db.refresh(new_cust)

    return CustomerResponse(
        id=new_cust.id,
        name=new_cust.name,
        phone=new_cust.phone,
        email=new_cust.email,
        address=new_cust.address,
        latitude=new_cust.latitude,
        longitude=new_cust.longitude,
        created_at=new_cust.created_at,
        updated_at=new_cust.updated_at,
        total_orders_count=0,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get single customer details."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return await _get_customer_with_orders_count(c, db)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_in: CustomerUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update customer details (Admin/Manager only)."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if customer_in.latitude is not None:
        if not (-90.0 <= customer_in.latitude <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude must be between -90 and 90",
            )
        c.latitude = customer_in.latitude

    if customer_in.longitude is not None:
        if not (-180.0 <= customer_in.longitude <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Longitude must be between -180 and 180",
            )
        c.longitude = customer_in.longitude

    if customer_in.name is not None:
        c.name = customer_in.name
    if customer_in.phone is not None:
        c.phone = customer_in.phone
    if customer_in.email is not None:
        c.email = customer_in.email
    if customer_in.address is not None:
        c.address = customer_in.address

    c.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(c)

    return await _get_customer_with_orders_count(c, db)


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete a customer record (Admin/Manager only)."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    await db.delete(c)
    await db.commit()
    return {"status": "success", "message": f"Customer {customer_id} deleted successfully"}
