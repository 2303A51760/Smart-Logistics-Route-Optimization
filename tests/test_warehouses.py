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
async def test_warehouse_crud_lifecycle(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Create warehouse
    create_payload = {
        "name": "Staten Island Hub",
        "address": "1500 Richmond Ave, Staten Island, NY",
        "latitude": 40.5795,
        "longitude": -74.1502,
        "capacity": 12000.0,
    }
    create_res = await async_client.post("/api/v1/warehouses", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    wh_data = create_res.json()
    wh_id = wh_data["id"]
    assert wh_data["name"] == "Staten Island Hub"
    assert wh_data["capacity"] == 12000.0

    # Get warehouse
    get_res = await async_client.get(f"/api/v1/warehouses/{wh_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Staten Island Hub"

    # Update warehouse
    update_payload = {"capacity": 14000.0, "name": "Staten Island Mega Hub"}
    put_res = await async_client.put(f"/api/v1/warehouses/{wh_id}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["capacity"] == 14000.0
    assert put_res.json()["name"] == "Staten Island Mega Hub"

    # Delete warehouse
    del_res = await async_client.delete(f"/api/v1/warehouses/{wh_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_warehouse_invalid_coordinates_and_capacity(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Latitude > 90
    bad_lat = {
        "name": "North Pole Warehouse",
        "address": "1 Arctic Way",
        "latitude": 95.0,
        "longitude": -74.0,
        "capacity": 5000.0,
    }
    res1 = await async_client.post("/api/v1/warehouses", json=bad_lat, headers=headers)
    assert res1.status_code == 422

    # Longitude < -180
    bad_lng = {
        "name": "Pacific Warehouse",
        "address": "1 Ocean Way",
        "latitude": 40.0,
        "longitude": -190.0,
        "capacity": 5000.0,
    }
    res2 = await async_client.post("/api/v1/warehouses", json=bad_lng, headers=headers)
    assert res2.status_code == 422

    # Capacity <= 0
    bad_cap = {
        "name": "Zero Cap Warehouse",
        "address": "1 Empty Way",
        "latitude": 40.0,
        "longitude": -74.0,
        "capacity": 0.0,
    }
    res3 = await async_client.post("/api/v1/warehouses", json=bad_cap, headers=headers)
    assert res3.status_code == 422
