import pytest
from httpx import AsyncClient


async def get_admin_token(client: AsyncClient) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin@123456"},
    )
    if res.status_code == 200:
        return res.json()["access_token"]
    return ""


@pytest.mark.asyncio
async def test_list_vehicles(async_client):
    token = await get_admin_token(async_client)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = await async_client.get("/api/v1/vehicles", headers=headers)
    assert response.status_code == 200
    data = response.json()
    items = data if isinstance(data, list) else data.get("items", [])
    assert len(items) >= 1
    assert "vehicle_number" in items[0] or "name" in items[0]


@pytest.mark.asyncio
async def test_list_routes(async_client):
    token = await get_admin_token(async_client)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = await async_client.get("/api/v1/routes", headers=headers)
    assert response.status_code == 200
    data = response.json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    assert len(items) >= 1
    assert "total_distance" in items[0] or "total_distance_km" in items[0]


@pytest.mark.asyncio
async def test_optimization_endpoint(async_client):
    payload = {
        "vehicle_ids": ["veh-101", "veh-102"],
        "delivery_ids": ["del-001", "del-002", "del-003"],
        "depot_lat": 40.7128,
        "depot_lng": -74.0060,
    }
    response = await async_client.post("/api/v1/optimization/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "routes" in data
    assert len(data["routes"]) >= 1
