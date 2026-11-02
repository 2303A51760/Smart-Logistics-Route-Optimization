import pytest
from httpx import AsyncClient
from app.services.dispatch_ai import dispatch_ai_engine


def test_dispatch_ai_ranking_logic():
    order = {
        "id": "ord-test-1",
        "order_number": "ORD-TEST-1",
        "package_weight": 50.0,
        "delivery_latitude": 40.7500,
        "delivery_longitude": -73.9800,
    }
    drivers = [
        {"id": "drv-1", "name": "Driver Active", "status": "AVAILABLE", "current_latitude": 40.7128, "current_longitude": -74.0060},
        {"id": "drv-2", "name": "Driver OffDuty", "status": "OFF_DUTY", "current_latitude": 40.9000, "current_longitude": -73.8000},
    ]
    vehicles = [
        {"id": "veh-1", "plate_number": "VAN-101", "capacity_kg": 500.0, "status": "AVAILABLE", "assigned_driver_id": "drv-1"},
        {"id": "veh-2", "plate_number": "VAN-102", "capacity_kg": 500.0, "status": "AVAILABLE", "assigned_driver_id": "drv-2"},
    ]
    warehouse = {"latitude": 40.7128, "longitude": -74.0060}

    recs = dispatch_ai_engine.rank_assignments_for_order(order, drivers, vehicles, warehouse)
    assert len(recs) == 2
    assert recs[0]["driver_id"] == "drv-1"
    assert recs[0]["score"] > recs[1]["score"]
    assert "Driver is currently on-duty" in recs[0]["reasons"][0]


def test_dispatch_ai_maintenance_safety():
    order = {"id": "ord-test-2", "package_weight": 10.0}
    drivers = [{"id": "drv-1", "name": "Driver 1", "status": "AVAILABLE"}]
    vehicles = [{"id": "veh-maint-1", "plate_number": "VAN-999", "capacity_kg": 500.0, "status": "MAINTENANCE", "assigned_driver_id": "drv-1"}]

    recs = dispatch_ai_engine.rank_assignments_for_order(order, drivers, vehicles)
    assert len(recs) == 0  # Maintenance vehicle must be safely excluded


@pytest.mark.asyncio
async def test_dispatch_recommendations_api(async_client: AsyncClient, manager_token_headers: dict):
    res = await async_client.get("/api/v1/ai/dispatch/recommendations", headers=manager_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert "total" in data
    if data["total"] > 0:
        first_rec = data["recommendations"][0]
        assert "driver_id" in first_rec
        assert "vehicle_id" in first_rec
        assert "score" in first_rec
        assert "reasons" in first_rec
