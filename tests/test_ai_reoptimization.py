import pytest
from httpx import AsyncClient
from app.services.dynamic_routing import dynamic_routing_engine


def test_dynamic_routing_engine_evaluation():
    warehouse = {"id": "wh-1", "latitude": 40.7128, "longitude": -74.0060}
    orders = [
        {"id": "o-1", "delivery_latitude": 40.7580, "delivery_longitude": -73.9855, "package_weight": 10.0},
        {"id": "o-2", "delivery_latitude": 40.7829, "delivery_longitude": -73.9654, "package_weight": 15.0},
    ]
    vehicles = [{"id": "v-1", "capacity_kg": 500.0, "plate_number": "VAN-01"}]
    drivers = [{"id": "d-1", "name": "Driver 1"}]

    res = dynamic_routing_engine.evaluate_reoptimization(
        route_id="route-test-101",
        warehouse=warehouse,
        current_orders=orders,
        vehicles=vehicles,
        drivers=drivers,
        current_distance_km=60.0,
        current_duration_minutes=120.0,
    )
    assert "reoptimization_beneficial" in res
    assert "original_distance_km" in res
    assert "optimized_distance_km" in res
    assert "estimated_fuel_saved_liters" in res
    assert "estimated_cost_saved" in res


@pytest.mark.asyncio
async def test_route_reoptimization_api(async_client: AsyncClient, manager_token_headers: dict):
    payload = {"trigger_reason": "Urgent order inserted into route"}
    res = await async_client.post("/api/v1/ai/routes/route-mock-1/reoptimize", json=payload, headers=manager_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["route_id"] == "route-mock-1"
    assert "reoptimization_beneficial" in data
    assert "reasons" in data
    assert "estimated_time_saved_minutes" in data
