import pytest
from httpx import AsyncClient
from app.services.order_priority import order_priority_engine


def test_order_priority_scoring_logic():
    # 1. Critical Order
    critical_order = {
        "id": "ord-crit-1",
        "order_number": "ORD-CRIT-1",
        "priority": "CRITICAL",
        "package_weight": 25.0,
        "time_window_end_sec": 7200,  # 2 hours
        "delivery_latitude": 40.8500,
        "delivery_longitude": -73.9000,
        "status": "PENDING",
    }
    crit_res = order_priority_engine.calculate_priority_score(critical_order)
    assert crit_res["score"] >= 80.0
    assert crit_res["priority"] in ["CRITICAL", "HIGH"]
    assert "Immediate delivery deadline" in crit_res["factors"]["deadline_factor_note"]

    # 2. Low Priority Order
    low_order = {
        "id": "ord-low-1",
        "order_number": "ORD-LOW-1",
        "priority": "LOW",
        "package_weight": 2.0,
        "time_window_end_sec": 86400,  # 24 hours
        "delivery_latitude": 40.7150,
        "delivery_longitude": -74.0020,
        "status": "DELIVERED",
    }
    low_res = order_priority_engine.calculate_priority_score(low_order)
    assert low_res["score"] < 50.0
    assert low_res["priority"] in ["LOW", "MEDIUM"]


@pytest.mark.asyncio
async def test_order_priority_api_endpoints(async_client: AsyncClient, admin_token_headers: dict):
    # List all order priorities
    res_list = await async_client.get("/api/v1/ai/order-priority", headers=admin_token_headers)
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert "total" in data_list
    assert len(data_list["orders"]) > 0

    first_order_id = data_list["orders"][0]["order_id"]

    # Get single order priority
    res_single = await async_client.get(f"/api/v1/ai/order-priority/{first_order_id}", headers=admin_token_headers)
    assert res_single.status_code == 200
    data_single = res_single.json()
    assert data_single["order_id"] == first_order_id
    assert "score" in data_single
    assert "factors" in data_single
    assert "reasons" in data_single


@pytest.mark.asyncio
async def test_order_priority_not_found(async_client: AsyncClient, admin_token_headers: dict):
    res = await async_client.get("/api/v1/ai/order-priority/non-existent-order-id-xyz", headers=admin_token_headers)
    assert res.status_code == 404
