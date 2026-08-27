import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, role_password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": role_password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_maintenance_crud_lifecycle(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create maintenance log
    create_payload = {
        "vehicle_id": "veh-101",
        "maintenance_type": "ENGINE_SERVICE",
        "mileage": 19000.0,
        "notes": "Comprehensive engine tuning and belt change.",
        "next_maintenance_mileage": 25000.0,
        "cost": 450.0,
        "status": "COMPLETED",
    }
    create_res = await async_client.post("/api/v1/maintenance", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    maint_data = create_res.json()
    maint_id = maint_data["id"]
    assert maint_data["vehicle_id"] == "veh-101"
    assert maint_data["maintenance_type"] == "ENGINE_SERVICE"
    assert maint_data["mileage"] == 19000.0
    assert maint_data["next_maintenance_mileage"] == 25000.0
    assert maint_data["cost"] == 450.0

    # 2. Get single maintenance record
    get_res = await async_client.get(f"/api/v1/maintenance/{maint_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == maint_id

    # 3. List maintenance records with filter
    list_res = await async_client.get("/api/v1/maintenance?vehicle_id=veh-101", headers=headers)
    assert list_res.status_code == 200
    records = list_res.json()
    assert any(r["id"] == maint_id for r in records)

    # 4. Update maintenance record
    put_res = await async_client.put(
        f"/api/v1/maintenance/{maint_id}",
        json={"notes": "Updated note: Spark plugs also replaced.", "cost": 500.0},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["cost"] == 500.0
    assert "Spark plugs" in put_res.json()["notes"]

    # 5. Delete maintenance record
    del_res = await async_client.delete(f"/api/v1/maintenance/{maint_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_maintenance_validation_rules(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Next maintenance mileage <= current service mileage
    invalid_mileage_payload = {
        "vehicle_id": "veh-101",
        "maintenance_type": "TIRE_ROTATION",
        "mileage": 15000.0,
        "next_maintenance_mileage": 14000.0,  # Invalid
        "cost": 100.0,
        "status": "COMPLETED",
    }
    res1 = await async_client.post("/api/v1/maintenance", json=invalid_mileage_payload, headers=headers)
    assert res1.status_code == 422

    # Nonexistent vehicle
    invalid_veh_payload = {
        "vehicle_id": "nonexistent-vehicle-xyz",
        "maintenance_type": "GENERAL_INSPECTION",
        "mileage": 5000.0,
        "next_maintenance_mileage": 10000.0,
        "cost": 50.0,
        "status": "COMPLETED",
    }
    res2 = await async_client.post("/api/v1/maintenance", json=invalid_veh_payload, headers=headers)
    assert res2.status_code == 404


@pytest.mark.asyncio
async def test_maintenance_rbac_driver_forbidden(async_client: AsyncClient):
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # Driver should get 403 Forbidden on list, create, delete maintenance
    res_list = await async_client.get("/api/v1/maintenance", headers=driver_headers)
    assert res_list.status_code == 403

    res_create = await async_client.post(
        "/api/v1/maintenance",
        json={"vehicle_id": "veh-101", "mileage": 1000.0, "next_maintenance_mileage": 5000.0},
        headers=driver_headers,
    )
    assert res_create.status_code == 403

    res_summary = await async_client.get("/api/v1/maintenance/dashboard/summary", headers=driver_headers)
    assert res_summary.status_code == 403


@pytest.mark.asyncio
async def test_maintenance_dashboard_summary_and_due(async_client: AsyncClient):
    manager_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {manager_token}"}

    # Test summary metrics
    sum_res = await async_client.get("/api/v1/maintenance/dashboard/summary", headers=headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_records"] >= 1
    assert "fleet_health_score" in summary
    assert "total_maintenance_cost" in summary
    assert "by_type" in summary

    # Test vehicles due
    due_res = await async_client.get("/api/v1/maintenance/due", headers=headers)
    assert due_res.status_code == 200
    due_list = due_res.json()
    assert len(due_list) >= 1
    # Check that veh-103 is marked overdue because its mileage (34,100) > next_maintenance_mileage (30,000)
    overdue_vehs = [v for v in due_list if v["is_overdue"]]
    assert len(overdue_vehs) >= 1
    assert any(v["vehicle_id"] == "veh-103" for v in overdue_vehs)
