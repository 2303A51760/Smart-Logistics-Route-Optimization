import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.order import Order
from app.models.user import UserRole
from app.core.security import create_access_token
from tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_order_persistence_across_sessions_and_restarts():
    """
    Explicitly proves database persistence:
    1. Create an order via HTTP API.
    2. Open a completely independent new DB session and confirm order exists.
    3. Simulate app/client restart with a fresh AsyncClient and retrieve order.
    4. Update order and verify persistent DB state in a new session.
    """
    manager_token = create_access_token(
        subject="usr-mgr-002",
        role=UserRole.LOGISTICS_MANAGER.value,
        name="Bob Logistics",
    )
    headers = {"Authorization": f"Bearer {manager_token}"}
    unique_order_number = f"ORD-PERSIST-{uuid.uuid4().hex[:6].upper()}"

    # Step 1: Create an order via first client session
    new_order_data = {
        "order_number": unique_order_number,
        "customer_id": "cust-001",
        "warehouse_id": "wh-001",
        "priority": "HIGH",
        "package_weight": 14.5,
        "pickup_latitude": 40.7128,
        "pickup_longitude": -74.0060,
        "pickup_address": "NYC Main Depot, New York, NY",
        "delivery_latitude": 40.7589,
        "delivery_longitude": -73.9851,
        "delivery_address": "Times Square, New York, NY",
    }

    transport1 = ASGITransport(app=app)
    async with AsyncClient(transport=transport1, base_url="http://test") as client1:
        res1 = await client1.post("/api/v1/orders", json=new_order_data, headers=headers)
        assert res1.status_code == 201, f"Create failed: {res1.text}"
        created = res1.json()
        order_id = created["id"]
        assert created["order_number"] == unique_order_number
        assert created["priority"] == "HIGH"

    # Step 2: Open a fresh, independent AsyncSession directly against DB
    async with TestAsyncSessionLocal() as db_session:
        query_res = await db_session.execute(select(Order).where(Order.id == order_id))
        db_order = query_res.scalar_one_or_none()
        assert db_order is not None, "Order was not persisted to the database!"
        assert db_order.order_number == unique_order_number
        assert float(db_order.package_weight) == 14.5
        assert float(db_order.delivery_latitude) == 40.7589
        assert float(db_order.delivery_longitude) == -73.9851

    # Step 3: Simulate app/client restart with a completely new AsyncClient
    transport2 = ASGITransport(app=app)
    async with AsyncClient(transport=transport2, base_url="http://test") as client2:
        res2 = await client2.get(f"/api/v1/orders/{order_id}", headers=headers)
        assert res2.status_code == 200, f"Retrieve failed: {res2.text}"
        retrieved = res2.json()
        assert retrieved["id"] == order_id
        assert retrieved["order_number"] == unique_order_number
        assert retrieved["package_weight"] == 14.5

    # Step 4: Update order via API and confirm persistence in a third independent session
    async with AsyncClient(transport=transport2, base_url="http://test") as client3:
        update_data = {"priority": "URGENT", "package_weight": 18.0}
        res3 = await client3.put(f"/api/v1/orders/{order_id}", json=update_data, headers=headers)
        assert res3.status_code == 200

    async with TestAsyncSessionLocal() as db_session2:
        query_res2 = await db_session2.execute(select(Order).where(Order.id == order_id))
        updated_db_order = query_res2.scalar_one_or_none()
        assert updated_db_order is not None
        assert updated_db_order.priority == "URGENT"
        assert float(updated_db_order.package_weight) == 18.0
