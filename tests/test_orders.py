import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, role_password: str = "Admin@123456") -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": role_password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_order_crud_and_lifecycle(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Create order
    create_payload = {
        "order_number": "ORD-TEST-8801",
        "customer_id": "cust-001",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": 35.5,
        "priority": "HIGH",
        "status": "PENDING",
        "assigned_driver_id": "drv-001",
    }
    create_res = await async_client.post("/api/v1/orders", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    order_data = create_res.json()
    order_id = order_data["id"]
    assert order_data["order_number"] == "ORD-TEST-8801"
    assert order_data["package_weight"] == 35.5
    assert order_data["priority"] == "HIGH"

    # Get single order
    get_res = await async_client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["customer_name"] == "Tech Hub Broadway"

    # Update order
    update_payload = {
        "status": "OUT_FOR_DELIVERY",
        "priority": "URGENT",
        "package_weight": 42.0,
    }
    put_res = await async_client.put(f"/api/v1/orders/{order_id}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "OUT_FOR_DELIVERY"
    assert put_res.json()["priority"] == "URGENT"

    # Delete order
    del_res = await async_client.delete(f"/api/v1/orders/{order_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_order_filtering_and_pagination(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # List with pagination
    res_page = await async_client.get("/api/v1/orders?page=1&size=2", headers=headers)
    assert res_page.status_code == 200
    data = res_page.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["size"] == 2

    # Filter by status
    res_status = await async_client.get("/api/v1/orders?status=PENDING", headers=headers)
    assert res_status.status_code == 200
    for item in res_status.json()["items"]:
        assert item["status"] == "PENDING"

    # Filter by priority
    res_pri = await async_client.get("/api/v1/orders?priority=URGENT", headers=headers)
    assert res_pri.status_code == 200
    for item in res_pri.json()["items"]:
        assert item["priority"] == "URGENT"

    # Search by order number
    res_search = await async_client.get("/api/v1/orders?search=7001", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_order_validations_and_foreign_keys(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Invalid weight <= 0
    bad_weight = {
        "order_number": "ORD-BAD-WT",
        "customer_id": "cust-001",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": -5.0,
    }
    res1 = await async_client.post("/api/v1/orders", json=bad_weight, headers=headers)
    assert res1.status_code == 422

    # 2. Nonexistent customer
    bad_cust = {
        "order_number": "ORD-BAD-CUST",
        "customer_id": "nonexistent-cust-99",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": 10.0,
    }
    res2 = await async_client.post("/api/v1/orders", json=bad_cust, headers=headers)
    assert res2.status_code == 400
    assert "customer" in res2.json()["detail"].lower()

    # 3. Nonexistent warehouse
    bad_wh = {
        "order_number": "ORD-BAD-WH",
        "customer_id": "cust-001",
        "warehouse_id": "nonexistent-wh-99",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": 10.0,
    }
    res3 = await async_client.post("/api/v1/orders", json=bad_wh, headers=headers)
    assert res3.status_code == 400
    assert "warehouse" in res3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_order_driver_role_restrictions(async_client: AsyncClient):
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    headers = {"Authorization": f"Bearer {driver_token}"}

    # Driver cannot create new orders
    create_payload = {
        "order_number": "ORD-DRV-FORBIDDEN",
        "customer_id": "cust-001",
        "warehouse_id": "wh-001",
        "pickup_latitude": 40.7538,
        "pickup_longitude": -74.0017,
        "delivery_latitude": 40.7209,
        "delivery_longitude": -74.0005,
        "package_weight": 10.0,
    }
    create_res = await async_client.post("/api/v1/orders", json=create_payload, headers=headers)
    assert create_res.status_code == 403

    # Driver cannot delete orders
    del_res = await async_client.delete("/api/v1/orders/ord-001", headers=headers)
    assert del_res.status_code == 403

    # Driver listing only includes assigned orders (e.g. ord-001, ord-002)
    list_res = await async_client.get("/api/v1/orders", headers=headers)
    assert list_res.status_code == 200
    for order in list_res.json()["items"]:
        assert order["assigned_driver_id"] == "drv-001"
