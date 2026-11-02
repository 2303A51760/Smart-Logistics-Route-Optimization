import pytest


@pytest.mark.asyncio
async def test_register_user_success(async_client):
    import time
    test_email = f"specialist_{int(time.time() * 1000)}@example.com"
    payload = {
        "name": "New Logistics Specialist",
        "email": test_email,
        "password": "SpecialistPass123!",
        "role": "LOGISTICS_MANAGER",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_email
    assert data["user"]["role"] == "LOGISTICS_MANAGER"


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client):
    payload = {
        "name": "Duplicate Admin",
        "email": "admin@example.com",
        "password": "Password123!",
        "role": "ADMIN",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_register_invalid_password(async_client):
    payload = {
        "name": "Short Pass User",
        "email": "short@example.com",
        "password": "123",  # Less than 6 characters
        "role": "DRIVER",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_demo_admin_success(async_client):
    payload = {
        "email": "admin@example.com",
        "password": "Admin@123456",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@example.com"
    assert data["user"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_login_demo_manager_success(async_client):
    payload = {
        "email": "manager@example.com",
        "password": "Manager@123456",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "LOGISTICS_MANAGER"


@pytest.mark.asyncio
async def test_login_demo_driver_success(async_client):
    payload = {
        "email": "driver@example.com",
        "password": "Driver@123456",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "DRIVER"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client):
    payload = {
        "email": "admin@example.com",
        "password": "WrongPassword!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client):
    payload = {
        "email": "nonexistent@example.com",
        "password": "RandomPassword123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_profile(async_client):
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin@123456"},
    )
    token = login_res.json()["access_token"]

    # 2. Get profile
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "admin@example.com"
    assert user_data["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_refresh_token_cycle(async_client):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "Manager@123456"},
    )
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout_endpoint(async_client):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "driver@example.com", "password": "Driver@123456"},
    )
    token = login_res.json()["access_token"]

    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"
