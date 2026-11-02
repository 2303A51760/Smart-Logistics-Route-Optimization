import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_driver_registration_and_dashboard_me_lifecycle(async_client: AsyncClient):
    """
    Test that registering a new DRIVER user automatically creates and links a Driver profile,
    and GET /api/v1/dashboard/driver-me succeeds with HTTP 200 returning the user's driver data.
    """
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    driver_email = f"new_driver_{timestamp}@example.com"
    driver_password = "Password@1234"
    driver_name = f"Registered Driver {timestamp}"

    # 1. Register a new user with role DRIVER
    res_reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": driver_email,
            "name": driver_name,
            "password": driver_password,
            "role": "DRIVER",
        },
    )
    assert res_reg.status_code in (200, 201)
    reg_data = res_reg.json()
    user_id = reg_data["user"]["id"]

    # 2. Login as the newly registered driver
    res_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": driver_email, "password": driver_password},
    )
    assert res_login.status_code == 200
    login_token = res_login.json()["access_token"]
    login_headers = {"Authorization": f"Bearer {login_token}"}

    # 3. GET /api/v1/dashboard/driver-me MUST return 200 OK (not 404)
    res_dash = await async_client.get("/api/v1/dashboard/driver-me", headers=login_headers)
    assert res_dash.status_code == 200
    dash_data = res_dash.json()

    # Verify driver profile returned belongs to the authenticated user
    assert dash_data["driver"] is not None
    assert dash_data["driver"]["user_id"] == user_id
    assert dash_data["driver"]["user_name"] == driver_name
    assert dash_data["driver"]["license_number"].startswith("DL-NY-")
    assert dash_data["stats"] is not None
    assert "completion_rate" in dash_data["stats"]
    assert "current_route" in dash_data

    # 4. GET /api/v1/drivers as DRIVER returns only their own driver profile
    res_drivers = await async_client.get("/api/v1/drivers", headers=login_headers)
    assert res_drivers.status_code == 200
    drivers_list = res_drivers.json()
    assert len(drivers_list) >= 1
    assert any(d["user_id"] == user_id for d in drivers_list)

    # 5. Verify calling /api/v1/dashboard/driver-me again does NOT create duplicate profiles
    res_dash_again = await async_client.get("/api/v1/dashboard/driver-me", headers=login_headers)
    assert res_dash_again.status_code == 200
    dash_again_data = res_dash_again.json()
    assert dash_again_data["driver"]["id"] == dash_data["driver"]["id"]


@pytest.mark.asyncio
async def test_seeded_driver_dashboard_me(async_client: AsyncClient):
    """
    Verify existing seeded driver account (driver@example.com) can access /api/v1/dashboard/driver-me.
    """
    res_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "driver@example.com", "password": "Driver@123456"},
    )
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_dash = await async_client.get("/api/v1/dashboard/driver-me", headers=headers)
    assert res_dash.status_code == 200
    data = res_dash.json()
    assert data["driver"]["id"] == "drv-001"
    assert data["driver"]["license_number"] == "DL-NY-893012"
