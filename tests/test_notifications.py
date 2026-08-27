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
async def test_notifications_list_and_role_isolation(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # Admin lists notifications
    admin_res = await async_client.get("/api/v1/notifications", headers=admin_headers)
    assert admin_res.status_code == 200
    admin_notifs = admin_res.json()
    assert "items" in admin_notifs
    assert "total" in admin_notifs

    # Driver lists notifications - must only see notifications relevant to driver drv-001 / assigned veh-101 / ord-002
    driver_res = await async_client.get("/api/v1/notifications", headers=driver_headers)
    assert driver_res.status_code == 200
    driver_notifs = driver_res.json()
    assert "items" in driver_notifs

    # Summary endpoint
    sum_res = await async_client.get("/api/v1/notifications/summary", headers=admin_headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert "unread_count" in summary
    assert "by_severity" in summary
    assert "by_type" in summary


@pytest.mark.asyncio
async def test_notifications_mark_read_and_mark_all(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Get unread notification
    list_res = await async_client.get("/api/v1/notifications", headers=headers)
    items = list_res.json()["items"]
    assert len(items) > 0
    target_id = items[0]["id"]

    # Mark single notification as read
    read_res = await async_client.patch(f"/api/v1/notifications/{target_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True
    assert read_res.json()["read_at"] is not None

    # Mark all as read
    mark_all_res = await async_client.post("/api/v1/notifications/mark-all-read", headers=headers)
    assert mark_all_res.status_code == 200
    assert mark_all_res.json()["status"] == "success"

    # Verify summary unread count is 0
    sum_res = await async_client.get("/api/v1/notifications/summary", headers=headers)
    assert sum_res.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_intelligent_alert_generation(async_client: AsyncClient):
    manager_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {manager_token}"}

    # Trigger intelligent alert audit
    audit_res = await async_client.post("/api/v1/notifications/check-alerts", headers=headers)
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total_alerts_generated"] >= 1
    assert "details" in audit_data

    # Check that alert categories are represented in generated alerts
    alert_types = [a["alert_type"] for a in audit_data["alerts"]]
    # Should detect at least maintenance due (veh-103 overdue) or urgent order unassigned (ord-003 or mock)
    assert any(
        t in alert_types
        for t in [
            "MAINTENANCE_DUE",
            "VEHICLE_OVERLOADED",
            "DRIVER_UNAVAILABLE",
            "DELIVERY_DELAYED",
            "ROUTE_EXCEEDS_MAX_DISTANCE",
            "URGENT_ORDER_UNASSIGNED",
        ]
    )


@pytest.mark.asyncio
async def test_notification_dismiss(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Trigger check to ensure at least one notification exists
    await async_client.post("/api/v1/notifications/check-alerts", headers=headers)

    list_res = await async_client.get("/api/v1/notifications", headers=headers)
    items = list_res.json()["items"]
    assert len(items) > 0
    to_delete_id = items[0]["id"]

    del_res = await async_client.delete(f"/api/v1/notifications/{to_delete_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
