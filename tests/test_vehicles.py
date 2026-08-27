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
async def test_vehicle_crud_lifecycle(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Create vehicle
    create_payload = {
        "vehicle_number": "TRK-EXP-9001",
        "vehicle_type": "TRUCK",
        "capacity": 3500.0,
        "fuel_type": "DIESEL",
        "mileage": 12000.0,
        "status": "AVAILABLE",
        "driver_id": "drv-002",
    }
    create_res = await async_client.post("/api/v1/vehicles", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    veh_data = create_res.json()
    veh_id = veh_data["id"]
    assert veh_data["vehicle_number"] == "TRK-EXP-9001"
    assert veh_data["capacity"] == 3500.0

    # Get single vehicle
    get_res = await async_client.get(f"/api/v1/vehicles/{veh_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["vehicle_number"] == "TRK-EXP-9001"

    # Update vehicle
    update_payload = {
        "capacity": 4000.0,
        "mileage": 12500.0,
        "status": "MAINTENANCE",
    }
    put_res = await async_client.put(f"/api/v1/vehicles/{veh_id}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["capacity"] == 4000.0
    assert put_res.json()["status"] == "MAINTENANCE"

    # Delete vehicle
    del_res = await async_client.delete(f"/api/v1/vehicles/{veh_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_vehicle_duplicate_number_rejected(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "vehicle_number": "NY-492-X",  # Seed vehicle
        "vehicle_type": "VAN",
        "capacity": 1000.0,
        "fuel_type": "DIESEL",
        "mileage": 500.0,
        "status": "AVAILABLE",
    }
    res = await async_client.post("/api/v1/vehicles", json=payload, headers=headers)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_vehicle_invalid_capacity_and_mileage(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Zero / negative capacity
    bad_cap_payload = {
        "vehicle_number": "TRK-BAD-CAP",
        "vehicle_type": "VAN",
        "capacity": 0.0,
        "mileage": 100.0,
    }
    res1 = await async_client.post("/api/v1/vehicles", json=bad_cap_payload, headers=headers)
    assert res1.status_code == 422

    # Negative mileage
    bad_mileage_payload = {
        "vehicle_number": "TRK-BAD-MIL",
        "vehicle_type": "VAN",
        "capacity": 1000.0,
        "mileage": -50.0,
    }
    res2 = await async_client.post("/api/v1/vehicles", json=bad_mileage_payload, headers=headers)
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_vehicle_nonexistent_driver_assignment(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "vehicle_number": "TRK-GHOST-DRV",
        "vehicle_type": "VAN",
        "capacity": 1000.0,
        "mileage": 10.0,
        "driver_id": "nonexistent-driver-999",
    }
    res = await async_client.post("/api/v1/vehicles", json=payload, headers=headers)
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"].lower()
