import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_operations_summary_rbac(
    async_client: AsyncClient,
    admin_token_headers: dict,
    manager_token_headers: dict,
    driver_token_headers: dict,
):
    # 1. Admin -> 200 OK
    res_admin = await async_client.get("/api/v1/ai/operations-summary", headers=admin_token_headers)
    assert res_admin.status_code == 200
    assert "critical_orders_count" in res_admin.json()

    # 2. Logistics Manager -> 200 OK
    res_mgr = await async_client.get("/api/v1/ai/operations-summary", headers=manager_token_headers)
    assert res_mgr.status_code == 200
    assert "recommended_assignments" in res_mgr.json()

    # 3. Driver -> 403 Forbidden (restricted management operational intelligence)
    res_drv = await async_client.get("/api/v1/ai/operations-summary", headers=driver_token_headers)
    assert res_drv.status_code == 403

    # 4. Unauthenticated -> 401 Unauthorized
    res_unauth = await async_client.get("/api/v1/ai/operations-summary")
    assert res_unauth.status_code == 401


@pytest.mark.asyncio
async def test_ai_dispatch_rbac(
    async_client: AsyncClient,
    manager_token_headers: dict,
    driver_token_headers: dict,
):
    # Manager -> 200 OK
    res_mgr = await async_client.get("/api/v1/ai/dispatch/recommendations", headers=manager_token_headers)
    assert res_mgr.status_code == 200

    # Driver -> 403 Forbidden
    res_drv = await async_client.get("/api/v1/ai/dispatch/recommendations", headers=driver_token_headers)
    assert res_drv.status_code == 403
