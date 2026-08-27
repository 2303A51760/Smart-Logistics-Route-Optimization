import pytest


async def get_token_for(async_client, email: str, password: str) -> str:
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_role_access(async_client):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin should access admin-only
    res = await async_client.get("/api/v1/auth/admin-only", headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "ADMIN"

    # Admin should access manager-only
    res = await async_client.get("/api/v1/auth/manager-only", headers=headers)
    assert res.status_code == 200

    # Admin should access driver-only
    res = await async_client.get("/api/v1/auth/driver-only", headers=headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_manager_role_access(async_client):
    manager_token = await get_token_for(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {manager_token}"}

    # Manager should be forbidden from admin-only
    res = await async_client.get("/api/v1/auth/admin-only", headers=headers)
    assert res.status_code == 403
    assert "Admin privileges required" in res.json()["detail"]

    # Manager should access manager-only
    res = await async_client.get("/api/v1/auth/manager-only", headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "LOGISTICS_MANAGER"

    # Manager should access driver-only
    res = await async_client.get("/api/v1/auth/driver-only", headers=headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_driver_role_access(async_client):
    driver_token = await get_token_for(async_client, "driver@example.com", "Driver@123456")
    headers = {"Authorization": f"Bearer {driver_token}"}

    # Driver should be forbidden from admin-only
    res = await async_client.get("/api/v1/auth/admin-only", headers=headers)
    assert res.status_code == 403

    # Driver should be forbidden from manager-only
    res = await async_client.get("/api/v1/auth/manager-only", headers=headers)
    assert res.status_code == 403
    assert "Manager or Admin privileges required" in res.json()["detail"]

    # Driver should access driver-only
    res = await async_client.get("/api/v1/auth/driver-only", headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "DRIVER"


@pytest.mark.asyncio
async def test_unauthenticated_access_rejected(async_client):
    res = await async_client.get("/api/v1/auth/admin-only")
    assert res.status_code == 401

    res = await async_client.get("/api/v1/auth/manager-only")
    assert res.status_code == 401

    res = await async_client.get("/api/v1/auth/driver-only")
    assert res.status_code == 401
