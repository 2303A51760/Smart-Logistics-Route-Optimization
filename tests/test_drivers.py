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
async def test_list_drivers_as_admin(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}
    res = await async_client.get("/api/v1/drivers", headers=headers)
    assert res.status_code == 200
    drivers = res.json()
    assert isinstance(drivers, list)
    assert len(drivers) >= 1


@pytest.mark.asyncio
async def test_create_and_delete_driver_as_manager(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Create driver
    driver_payload = {
        "license_number": "DL-TEST-99901",
        "phone": "+1-555-0988",
        "status": "AVAILABLE",
        "current_latitude": 40.7128,
        "current_longitude": -74.0060,
    }
    create_res = await async_client.post("/api/v1/drivers", json=driver_payload, headers=headers)
    assert create_res.status_code == 201
    driver_data = create_res.json()
    assert driver_data["license_number"] == "DL-TEST-99901"
    driver_id = driver_data["id"]

    # Read driver
    get_res = await async_client.get(f"/api/v1/drivers/{driver_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["phone"] == "+1-555-0988"

    # Update driver
    update_payload = {"phone": "+1-555-9999", "status": "IN_TRANSIT"}
    put_res = await async_client.put(f"/api/v1/drivers/{driver_id}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["phone"] == "+1-555-9999"
    assert put_res.json()["status"] == "IN_TRANSIT"

    # Delete driver
    del_res = await async_client.delete(f"/api/v1/drivers/{driver_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_create_driver_duplicate_license(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "license_number": "DL-NY-893012",  # Existing seed driver license
        "phone": "+1-555-0000",
        "status": "AVAILABLE",
    }
    res = await async_client.post("/api/v1/drivers", json=payload, headers=headers)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_driver_role_permission_restriction(async_client: AsyncClient):
    # Driver account cannot create or delete drivers
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    headers = {"Authorization": f"Bearer {driver_token}"}

    payload = {
        "license_number": "DL-HACK-0001",
        "phone": "+1-555-1111",
        "status": "AVAILABLE",
    }
    create_res = await async_client.post("/api/v1/drivers", json=payload, headers=headers)
    assert create_res.status_code == 403

    del_res = await async_client.delete("/api/v1/drivers/drv-001", headers=headers)
    assert del_res.status_code == 403
