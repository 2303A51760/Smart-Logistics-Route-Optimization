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
async def test_dashboard_overview_as_admin_and_manager(async_client: AsyncClient):
    # Admin
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await async_client.get("/api/v1/dashboard/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "orders" in data
    assert "drivers" in data
    assert "vehicles" in data
    assert "delivery" in data
    assert data["orders"]["total"] >= 1
    assert data["drivers"]["total"] >= 1
    assert data["vehicles"]["total"] >= 1

    # Logistics Manager
    mgr_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers_mgr = {"Authorization": f"Bearer {mgr_token}"}
    res_mgr = await async_client.get("/api/v1/dashboard/overview", headers=headers_mgr)
    assert res_mgr.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_overview_rejected_for_driver(async_client: AsyncClient):
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    headers = {"Authorization": f"Bearer {driver_token}"}
    res = await async_client.get("/api/v1/dashboard/overview", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_order_analytics_trends(async_client: AsyncClient):
    mgr_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {mgr_token}"}
    res = await async_client.get("/api/v1/dashboard/orders?days=7", headers=headers)
    assert res.status_code == 200
    trends = res.json()
    assert isinstance(trends, list)
    assert len(trends) == 7
    assert "date" in trends[0]
    assert "total" in trends[0]


@pytest.mark.asyncio
async def test_driver_performance_metrics(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await async_client.get("/api/v1/dashboard/driver-performance", headers=headers)
    assert res.status_code == 200
    perf = res.json()
    assert isinstance(perf, list)
    assert len(perf) >= 1
    assert "completion_rate" in perf[0]
    assert "assigned_deliveries" in perf[0]


@pytest.mark.asyncio
async def test_vehicle_utilization_metrics(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await async_client.get("/api/v1/dashboard/vehicle-utilization", headers=headers)
    assert res.status_code == 200
    util = res.json()
    assert "items" in util
    assert "status_summary" in util
    assert len(util["items"]) >= 1


@pytest.mark.asyncio
async def test_driver_me_isolated_dashboard(async_client: AsyncClient):
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    headers = {"Authorization": f"Bearer {driver_token}"}
    res = await async_client.get("/api/v1/dashboard/driver-me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "driver" in data
    assert "stats" in data
    assert "assigned_orders" in data
    assert data["driver"]["user_id"] == "usr-drv-003"
    for order in data["assigned_orders"]:
        assert order["assigned_driver_id"] == data["driver"]["id"]
