import pytest
from httpx import AsyncClient
from datetime import datetime


async def get_token_for(client: AsyncClient, email: str, password: str = "Admin@123456") -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# ==========================================
# 1. AUDIT LOG GENERATION ON AUTH LIFECYCLE
# ==========================================
@pytest.mark.asyncio
async def test_audit_log_created_on_registration_and_login(async_client: AsyncClient):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    timestamp = int(datetime.utcnow().timestamp())
    test_email = f"audit_user_{timestamp}@example.com"

    # 1. Register a new user
    res_reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": test_email,
            "name": "Audit Test User",
            "password": "Password@123",
            "role": "DRIVER",
        },
    )
    assert res_reg.status_code in [200, 201]

    # 2. Login with bad password -> triggers LOGIN_FAILED audit
    res_bad_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": "WrongPassword999!"},
    )
    assert res_bad_login.status_code in [400, 401]

    # 3. Login successfully -> triggers USER_LOGIN audit
    res_good_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": "Password@123"},
    )
    assert res_good_login.status_code == 200

    # 4. Check audit logs as Admin
    res_logs = await async_client.get(
        f"/api/v1/audit-logs?search={test_email}",
        headers=admin_headers,
    )
    assert res_logs.status_code == 200
    data = res_logs.json()
    assert data["total"] >= 2
    actions = [item["action"] for item in data["items"]]
    assert "USER_REGISTER" in actions
    assert "LOGIN_FAILED" in actions or "USER_LOGIN" in actions


# ==========================================
# 2. AUDIT LOGS RBAC ENFORCEMENT
# ==========================================
@pytest.mark.asyncio
async def test_audit_logs_rbac_driver_forbidden(async_client: AsyncClient):
    # Driver login
    driver_token = await get_token_for(async_client, "driver@example.com", "Driver@123456")
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # Driver attempts to access global audit logs -> MUST be 403 Forbidden
    res = await async_client.get("/api/v1/audit-logs", headers=driver_headers)
    assert res.status_code == 403
    assert "Drivers are not authorized" in res.json()["detail"]

    # Driver attempts to access single audit log ID -> MUST be 403 Forbidden
    res_single = await async_client.get("/api/v1/audit-logs/audit-001", headers=driver_headers)
    assert res_single.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_manager_and_admin_access(async_client: AsyncClient):
    # Manager access
    mgr_token = await get_token_for(async_client, "manager@example.com", "Manager@123456")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    res_mgr = await async_client.get("/api/v1/audit-logs", headers=mgr_headers)
    assert res_mgr.status_code == 200
    assert "items" in res_mgr.json()

    # Admin access
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res_admin = await async_client.get("/api/v1/audit-logs", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["total"] >= 1


# ==========================================
# 3. FILTERING & PAGINATION
# ==========================================
@pytest.mark.asyncio
async def test_audit_logs_filtering_and_pagination(async_client: AsyncClient):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Filter by resource_type
    res_resource = await async_client.get("/api/v1/audit-logs?resource_type=AUTH", headers=admin_headers)
    assert res_resource.status_code == 200
    for item in res_resource.json()["items"]:
        assert item["resource_type"] == "AUTH"

    # Filter by success
    res_success = await async_client.get("/api/v1/audit-logs?success=true", headers=admin_headers)
    assert res_success.status_code == 200
    for item in res_success.json()["items"]:
        assert item["success"] is True

    # Pagination
    res_page = await async_client.get("/api/v1/audit-logs?page=1&limit=2", headers=admin_headers)
    assert res_page.status_code == 200
    paged_data = res_page.json()
    assert len(paged_data["items"]) <= 2
    assert paged_data["page"] == 1
    assert paged_data["limit"] == 2


# ==========================================
# 4. AUDIT SUMMARY ANALYTICS
# ==========================================
@pytest.mark.asyncio
async def test_audit_summary_analytics(async_client: AsyncClient):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res = await async_client.get("/api/v1/audit-logs/summary", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_events" in data
    assert "successful_events" in data
    assert "failed_events" in data
    assert "unauthorized_attempts" in data
    assert "actions_by_role" in data
    assert "top_actions" in data
    assert "recent_security_events" in data


# ==========================================
# 5. SECURITY HEADERS VERIFICATION
# ==========================================
@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    res = await async_client.get("/")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "1; mode=block" in headers.get("X-XSS-Protection", "")
    assert "max-age=" in headers.get("Strict-Transport-Security", "")


# ==========================================
# 6. OPERATIONAL AUDIT TRIGGERING
# ==========================================
@pytest.mark.asyncio
async def test_operational_audit_logging_on_optimization_and_maintenance(async_client: AsyncClient):
    admin_token = await get_token_for(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Trigger Route Optimization
    res_opt = await async_client.post(
        "/api/v1/optimization/optimize",
        json={"warehouse_id": "wh-001", "order_ids": ["ord-001"]},
        headers=admin_headers,
    )
    assert res_opt.status_code == 200

    # 2. Trigger Maintenance Record Creation
    res_maint = await async_client.post(
        "/api/v1/maintenance",
        json={
            "vehicle_id": "veh-101",
            "maintenance_type": "OIL_CHANGE",
            "mileage": 15000.0,
            "next_maintenance_mileage": 20000.0,
            "cost": 150.0,
            "status": "COMPLETED",
        },
        headers=admin_headers,
    )
    assert res_maint.status_code in [200, 201]
    assert res_maint.json()["id"] is not None

    # 3. Verify audit log captures these actions
    res_logs = await async_client.get("/api/v1/audit-logs?limit=20", headers=admin_headers)
    assert res_logs.status_code == 200
    actions = [x["action"] for x in res_logs.json()["items"]]
    assert "ROUTE_OPTIMIZE" in actions
    assert "MAINTENANCE_CREATE" in actions


# ==========================================
# 7. DIRECT RATE LIMITER UNIT TEST
# ==========================================
@pytest.mark.asyncio
async def test_rate_limiter_logic():
    from app.core.rate_limiter import RateLimiter

    limiter = RateLimiter(requests_limit=3, window_seconds=2)
    test_key = "unit_test_ip_123"

    # Requests 1, 2, 3 succeed
    is_limited, rem1 = await limiter.is_rate_limited(test_key)
    assert is_limited is False
    assert rem1 == 2

    is_limited, rem2 = await limiter.is_rate_limited(test_key)
    assert is_limited is False
    assert rem2 == 1

    is_limited, rem3 = await limiter.is_rate_limited(test_key)
    assert is_limited is False
    assert rem3 == 0

    # Request 4 is rate limited
    is_limited, rem4 = await limiter.is_rate_limited(test_key)
    assert is_limited is True
    assert rem4 == 0
