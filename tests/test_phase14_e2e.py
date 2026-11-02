import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_phase14_complete_ai_dispatch_workflow(
    async_client: AsyncClient,
    admin_token_headers: dict,
):
    # Step 1: Order Priority Scoring
    res_prio = await async_client.get("/api/v1/ai/order-priority", headers=admin_token_headers)
    assert res_prio.status_code == 200
    prio_data = res_prio.json()
    assert prio_data["total"] > 0
    target_order = prio_data["orders"][0]
    order_id = target_order["order_id"]

    # Step 2: Delay Risk Evaluation
    res_delay = await async_client.get(f"/api/v1/ai/delay-risk/order/{order_id}", headers=admin_token_headers)
    assert res_delay.status_code == 200
    assert "delay_probability" in res_delay.json()

    # Step 3: AI-Assisted Dispatch Matching
    res_dispatch = await async_client.get(f"/api/v1/ai/dispatch/recommendations?order_id={order_id}", headers=admin_token_headers)
    assert res_dispatch.status_code == 200
    assert "recommendations" in res_dispatch.json()

    # Step 4: Dynamic Route Re-Optimization
    res_reopt = await async_client.post(
        "/api/v1/ai/routes/route-mock-e2e/reoptimize",
        json={"trigger_reason": "High priority order scheduled"},
        headers=admin_token_headers,
    )
    assert res_reopt.status_code == 200
    assert "reoptimization_beneficial" in res_reopt.json()

    # Step 5: Operations Summary Aggregation
    res_summary = await async_client.get("/api/v1/ai/operations-summary", headers=admin_token_headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert "critical_orders_count" in summary
    assert "estimated_fleet_time_saved_minutes" in summary
    assert "demand_forecast_glance" in summary
