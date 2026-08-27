import pytest
from httpx import AsyncClient
from datetime import datetime


async def get_token_for(client: AsyncClient, email: str, password: str = "Admin@123456") -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# ==========================================
# 1. ROOT, HEALTH, DOCS & OPENAPI
# ==========================================
@pytest.mark.asyncio
async def test_backend_root_health_and_openapi(async_client: AsyncClient):
    # Root
    res_root = await async_client.get("/")
    assert res_root.status_code == 200
    assert "version" in res_root.json()

    # Health
    res_health = await async_client.get("/api/v1/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] in ["healthy", "degraded", "online", "ok"]
    assert "services" in health_data


# ==========================================
# 2. AUTHENTICATION & RBAC VALIDATION
# ==========================================
@pytest.mark.asyncio
async def test_auth_registration_lifecycle(async_client: AsyncClient):
    timestamp = int(datetime.utcnow().timestamp())
    test_email = f"phase11_user_{timestamp}@example.com"
    payload = {
        "email": test_email,
        "name": "Phase 11 Tester",
        "password": "Password@123",
        "role": "LOGISTICS_MANAGER",
    }

    # 1. Valid registration
    res_reg = await async_client.post("/api/v1/auth/register", json=payload)
    assert res_reg.status_code in [200, 201]
    reg_data = res_reg.json()
    assert reg_data["user"]["email"] == test_email
    assert "access_token" in reg_data

    # 2. Duplicate registration rejected
    res_dup = await async_client.post("/api/v1/auth/register", json=payload)
    assert res_dup.status_code in [400, 409]

    # 3. Successful login with newly created account
    res_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": "Password@123"},
    )
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

    # 4. Invalid login rejected with 401/400 (never 500)
    res_bad_pw = await async_client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": "WrongPassword999!"},
    )
    assert res_bad_pw.status_code in [400, 401]

    # 5. Nonexistent user login rejected
    res_ghost = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_ghost_999@example.com", "password": "Password@123"},
    )
    assert res_ghost.status_code in [400, 401, 404]


@pytest.mark.asyncio
async def test_protected_endpoints_auth_enforcement(async_client: AsyncClient):
    # Unauthenticated access rejected
    res_unauth = await async_client.get("/api/v1/auth/me")
    assert res_unauth.status_code in [401, 403]

    # Authenticated access succeeds
    token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    res_auth = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    assert res_auth.json()["email"] == "admin@example.com"


# ==========================================
# 3. ROUTE OPTIMIZATION TESTING
# ==========================================
@pytest.mark.asyncio
async def test_route_optimizer_empty_input(async_client: AsyncClient):
    token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Empty order_ids
    payload = {
        "warehouse_id": "wh-001",
        "order_ids": [],
        "driver_ids": [],
        "vehicle_ids": [],
    }
    res = await async_client.post("/api/v1/optimization/optimize", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["SUCCESS", "NO_ORDERS", "COMPLETED"]
    assert "routes" in data


@pytest.mark.asyncio
async def test_route_optimizer_single_and_multiple_locations(async_client: AsyncClient):
    token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Single order optimization
    payload_single = {
        "warehouse_id": "wh-001",
        "order_ids": ["ord-001"],
    }
    res_single = await async_client.post("/api/v1/optimization/optimize", json=payload_single, headers=headers)
    assert res_single.status_code == 200
    data_single = res_single.json()
    assert data_single["orders_assigned"] == 1
    assert len(data_single["routes"]) >= 1

    # Multiple orders optimization
    payload_multi = {
        "warehouse_id": "wh-001",
        "order_ids": ["ord-001", "ord-002"],
    }
    res_multi = await async_client.post("/api/v1/optimization/optimize", json=payload_multi, headers=headers)
    assert res_multi.status_code == 200
    data_multi = res_multi.json()
    assert data_multi["orders_assigned"] == 2
    assert "total_distance_km" in data_multi
    assert "total_duration_min" in data_multi


@pytest.mark.asyncio
async def test_route_optimizer_legacy_solve_endpoint(async_client: AsyncClient):
    # Test solve endpoint directly (standalone coordinates: Hyderabad/custom matrix)
    payload = {
        "vehicle_ids": ["veh-01", "veh-02"],
        "delivery_ids": ["loc-1", "loc-2", "loc-3", "loc-4"],
        "depot_lat": 17.3850,
        "depot_lng": 78.4867,
    }
    res = await async_client.post("/api/v1/optimization/solve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["num_stops"] == 4
    assert len(data["routes"]) >= 1
    assert data["total_distance_km"] > 0


@pytest.mark.asyncio
async def test_route_optimizer_invalid_warehouse(async_client: AsyncClient):
    token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "warehouse_id": "nonexistent-warehouse-999",
        "order_ids": ["ord-001"],
    }
    res = await async_client.post("/api/v1/optimization/optimize", json=payload, headers=headers)
    assert res.status_code == 404


# ==========================================
# 4. API TEST MATRIX ACROSS ALL DOMAINS
# ==========================================
@pytest.mark.asyncio
async def test_complete_api_matrix(async_client: AsyncClient):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Orders
    res_orders = await async_client.get("/api/v1/orders", headers=admin_headers)
    assert res_orders.status_code == 200
    assert "items" in res_orders.json()

    # 2. Drivers
    res_drivers = await async_client.get("/api/v1/drivers", headers=admin_headers)
    assert res_drivers.status_code == 200
    assert isinstance(res_drivers.json(), list)

    # 3. Vehicles
    res_vehicles = await async_client.get("/api/v1/vehicles", headers=admin_headers)
    assert res_vehicles.status_code == 200
    assert isinstance(res_vehicles.json(), list)

    # 4. Warehouses
    res_wh = await async_client.get("/api/v1/warehouses", headers=admin_headers)
    assert res_wh.status_code == 200
    assert isinstance(res_wh.json(), list)

    # 5. Customers
    res_cust = await async_client.get("/api/v1/customers", headers=admin_headers)
    assert res_cust.status_code == 200
    assert isinstance(res_cust.json(), list)

    # 6. Routes
    res_routes = await async_client.get("/api/v1/routes", headers=admin_headers)
    assert res_routes.status_code == 200
    assert "items" in res_routes.json() or isinstance(res_routes.json(), list)

    # 7. Dashboard overview
    res_dash = await async_client.get("/api/v1/dashboard/overview", headers=admin_headers)
    assert res_dash.status_code == 200
    assert "orders" in res_dash.json()
    assert "drivers" in res_dash.json()

    # 8. Map overview
    res_map = await async_client.get("/api/v1/map/overview", headers=admin_headers)
    assert res_map.status_code == 200
    assert "drivers" in res_map.json()
    assert "warehouses" in res_map.json()

    # 9. AI ETA prediction
    res_eta = await async_client.post(
        "/api/v1/eta/predict",
        json={
            "origin_lat": 40.7538,
            "origin_lng": -74.0017,
            "destination_lat": 40.7209,
            "destination_lng": -74.0005,
            "distance_km": 5.2,
            "package_weight": 10.0,
            "priority": "HIGH",
        },
        headers=admin_headers,
    )
    assert res_eta.status_code == 200
    assert "predicted_duration_minutes" in res_eta.json()

    # 10. AI Demand Forecast
    res_forecast = await async_client.get("/api/v1/forecast/demand?horizon=7", headers=admin_headers)
    assert res_forecast.status_code == 200
    assert "forecast" in res_forecast.json()

    # 11. Maintenance
    res_maint = await async_client.get("/api/v1/maintenance", headers=admin_headers)
    assert res_maint.status_code == 200
    assert isinstance(res_maint.json(), list)

    # 12. Notifications
    res_notif = await async_client.get("/api/v1/notifications", headers=admin_headers)
    assert res_notif.status_code == 200
    assert "items" in res_notif.json()


# ==========================================
# 5. ERROR HANDLING TESTS
# ==========================================
@pytest.mark.asyncio
async def test_error_handling_edge_cases(async_client: AsyncClient):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Nonexistent resource (404)
    res_404 = await async_client.get("/api/v1/orders/nonexistent-order-id-12345", headers=admin_headers)
    assert res_404.status_code == 404

    # 2. Missing required fields in POST (422)
    res_422 = await async_client.post("/api/v1/customers", json={"name": ""}, headers=admin_headers)
    assert res_422.status_code == 422

    # 3. Invalid vehicle capacity (422)
    res_bad_cap = await async_client.post(
        "/api/v1/vehicles",
        json={"vehicle_number": "TEST-CAP", "capacity": -10.0},
        headers=admin_headers,
    )
    assert res_bad_cap.status_code == 422
