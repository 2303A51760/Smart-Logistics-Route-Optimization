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
async def test_map_overview_as_admin_and_manager(async_client: AsyncClient):
    # Admin
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await async_client.get("/api/v1/map/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "drivers" in data
    assert "warehouses" in data
    assert "orders" in data
    assert len(data["warehouses"]) >= 1
    assert len(data["drivers"]) >= 1
    assert len(data["orders"]) >= 1

    # Check coordinate bounds
    for w in data["warehouses"]:
        assert -90 <= w["latitude"] <= 90
        assert -180 <= w["longitude"] <= 180

    for d in data["drivers"]:
        assert -90 <= d["latitude"] <= 90
        assert -180 <= d["longitude"] <= 180

    for o in data["orders"]:
        assert -90 <= o["pickup_latitude"] <= 90
        assert -180 <= o["delivery_longitude"] <= 180

    # Logistics Manager
    mgr_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers_mgr = {"Authorization": f"Bearer {mgr_token}"}
    res_mgr = await async_client.get("/api/v1/map/overview", headers=headers_mgr)
    assert res_mgr.status_code == 200


@pytest.mark.asyncio
async def test_map_overview_driver_scoping_and_isolation(async_client: AsyncClient):
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    headers = {"Authorization": f"Bearer {driver_token}"}
    res = await async_client.get("/api/v1/map/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "drivers" in data
    assert "warehouses" in data
    assert "orders" in data
    # Driver only sees their own driver marker (at most 1)
    assert len(data["drivers"]) <= 1
    # All orders shown to driver must be assigned to this driver
    if len(data["drivers"]) == 1:
        my_driver_id = data["drivers"][0]["id"]
        for o in data["orders"]:
            assert o["assigned_driver_id"] == my_driver_id


@pytest.mark.asyncio
async def test_map_overview_unauthorized(async_client: AsyncClient):
    res = await async_client.get("/api/v1/map/overview")
    assert res.status_code == 401
