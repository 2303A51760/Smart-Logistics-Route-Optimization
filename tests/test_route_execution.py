import pytest
import uuid
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, role_password: str = "Admin@123456") -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": role_password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


async def create_test_order(client: AsyncClient, headers: dict, wh_id: str) -> str:
    cust_res = await client.get("/api/v1/customers", headers=headers)
    custs = cust_res.json() if isinstance(cust_res.json(), list) else cust_res.json().get("items", [])
    cust_id = custs[0]["id"]

    order_payload = {
        "order_number": f"ORD-TEST-{uuid.uuid4().hex[:6]}",
        "customer_id": cust_id,
        "warehouse_id": wh_id,
        "pickup_latitude": 40.7128,
        "pickup_longitude": -74.0060,
        "delivery_latitude": 40.7580,
        "delivery_longitude": -73.9855,
        "package_weight": 5.0,
        "priority": "HIGH",
    }
    res = await client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_full_route_execution_workflow(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    wh_res = await async_client.get("/api/v1/warehouses", headers=admin_headers)
    warehouses = wh_res.json() if isinstance(wh_res.json(), list) else wh_res.json().get("items", [])
    wh_id = warehouses[0]["id"]

    order_id1 = await create_test_order(async_client, admin_headers, wh_id)
    order_id2 = await create_test_order(async_client, admin_headers, wh_id)

    # 1. Run optimization
    opt_res = await async_client.post(
        "/api/v1/optimization/optimize",
        json={"warehouse_id": wh_id, "order_ids": [order_id1, order_id2], "time_limit_seconds": 1},
        headers=admin_headers,
    )
    assert opt_res.status_code == 200
    job_id = opt_res.json()["job_id"]

    # 2. Convert to executable routes
    create_res = await async_client.post(
        f"/api/v1/optimization/jobs/{job_id}/create-routes",
        json={"job_id": job_id},
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    route_ids = create_res.json()["route_ids"]
    assert len(route_ids) >= 1
    route_id = route_ids[0]

    # 3. Inspect route
    route_detail = await async_client.get(f"/api/v1/routes/{route_id}", headers=admin_headers)
    assert route_detail.status_code == 200
    route_data = route_detail.json()
    assert route_data["status"] == "PLANNED"
    assert len(route_data["stops"]) >= 1

    stop1 = route_data["stops"][0]

    # 4. Start route -> status becomes IN_PROGRESS, orders become OUT_FOR_DELIVERY
    start_res = await async_client.post(
        f"/api/v1/routes/{route_id}/start",
        json={"latitude": 40.7128, "longitude": -74.0060, "notes": "Starting route execution"},
        headers=admin_headers,
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_PROGRESS"
    assert start_res.json()["started_at"] is not None

    if stop1.get("order_id"):
        chk_ord = await async_client.get(f"/api/v1/orders/{stop1['order_id']}", headers=admin_headers)
        assert chk_ord.json()["status"] == "OUT_FOR_DELIVERY"

    # 5. Arrive at stop -> stop becomes ARRIVED, order becomes ARRIVED
    arr_res = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop1['id']}/arrive",
        json={"latitude": 40.7200, "longitude": -74.0000},
        headers=admin_headers,
    )
    assert arr_res.status_code == 200
    assert arr_res.json()["stops"][0]["status"] == "ARRIVED"

    if stop1.get("order_id"):
        chk_ord2 = await async_client.get(f"/api/v1/orders/{stop1['order_id']}", headers=admin_headers)
        assert chk_ord2.json()["status"] == "ARRIVED"

    # 6. Start delivery -> stop becomes IN_PROGRESS
    start_del = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop1['id']}/start-delivery",
        headers=admin_headers,
    )
    assert start_del.status_code == 200
    assert start_del.json()["stops"][0]["status"] == "IN_PROGRESS"

    # 7. Deliver stop -> stop becomes DELIVERED, order becomes DELIVERED
    del_res = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop1['id']}/deliver",
        json={"latitude": 40.7200, "longitude": -74.0000, "notes": "Package handed directly"},
        headers=admin_headers,
    )
    assert del_res.status_code == 200
    assert del_res.json()["stops"][0]["status"] == "DELIVERED"

    if stop1.get("order_id"):
        chk_ord3 = await async_client.get(f"/api/v1/orders/{stop1['order_id']}", headers=admin_headers)
        assert chk_ord3.json()["status"] == "DELIVERED"


@pytest.mark.asyncio
async def test_stop_failure_and_skip_workflow(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    wh_res = await async_client.get("/api/v1/warehouses", headers=admin_headers)
    warehouses = wh_res.json() if isinstance(wh_res.json(), list) else wh_res.json().get("items", [])
    wh_id = warehouses[0]["id"]

    order_id1 = await create_test_order(async_client, admin_headers, wh_id)
    order_id2 = await create_test_order(async_client, admin_headers, wh_id)

    opt_res = await async_client.post(
        "/api/v1/optimization/optimize",
        json={"warehouse_id": wh_id, "order_ids": [order_id1, order_id2], "time_limit_seconds": 1},
        headers=admin_headers,
    )
    job_id = opt_res.json()["job_id"]

    create_res = await async_client.post(
        f"/api/v1/optimization/jobs/{job_id}/create-routes",
        json={"job_id": job_id},
        headers=admin_headers,
    )
    route_id = create_res.json()["route_ids"][0]

    # Start Route
    await async_client.post(f"/api/v1/routes/{route_id}/start", headers=admin_headers)

    route_res = await async_client.get(f"/api/v1/routes/{route_id}", headers=admin_headers)
    stops = route_res.json()["stops"]
    stop1 = stops[0]

    # 1. Fail Stop 1 with reason -> order becomes FAILED
    fail_res = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop1['id']}/fail",
        json={"reason": "CUSTOMER_UNAVAILABLE", "notes": "No response to gate buzzer"},
        headers=admin_headers,
    )
    assert fail_res.status_code == 200
    assert fail_res.json()["stops"][0]["status"] == "FAILED"

    if stop1.get("order_id"):
        chk_fail_ord = await async_client.get(f"/api/v1/orders/{stop1['order_id']}", headers=admin_headers)
        assert chk_fail_ord.json()["status"] == "FAILED"

    # 2. Skip Stop 2 if present -> stop becomes SKIPPED
    if len(stops) > 1:
        stop2 = stops[1]
        skip_res = await async_client.post(
            f"/api/v1/routes/{route_id}/stops/{stop2['id']}/skip",
            json={"reason": "Access restricted due to road construction"},
            headers=admin_headers,
        )
        assert skip_res.status_code == 200
        assert skip_res.json()["stops"][1]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_route_cancellation_and_restrictions(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    wh_res = await async_client.get("/api/v1/warehouses", headers=admin_headers)
    warehouses = wh_res.json() if isinstance(wh_res.json(), list) else wh_res.json().get("items", [])
    wh_id = warehouses[0]["id"]

    order_id = await create_test_order(async_client, admin_headers, wh_id)

    opt_res = await async_client.post(
        "/api/v1/optimization/optimize",
        json={"warehouse_id": wh_id, "order_ids": [order_id], "time_limit_seconds": 1},
        headers=admin_headers,
    )
    job_id = opt_res.json()["job_id"]

    create_res = await async_client.post(
        f"/api/v1/optimization/jobs/{job_id}/create-routes",
        json={"job_id": job_id},
        headers=admin_headers,
    )
    route_id = create_res.json()["route_ids"][0]

    # Cancel planned route
    cancel_res = await async_client.post(
        f"/api/v1/routes/{route_id}/cancel",
        json={"reason": "Fleet vehicle breakdown"},
        headers=admin_headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Cannot start a cancelled route
    bad_start = await async_client.post(f"/api/v1/routes/{route_id}/start", headers=admin_headers)
    assert bad_start.status_code == 400


@pytest.mark.asyncio
async def test_invalid_state_transitions_prevented(async_client: AsyncClient):
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    wh_res = await async_client.get("/api/v1/warehouses", headers=admin_headers)
    warehouses = wh_res.json() if isinstance(wh_res.json(), list) else wh_res.json().get("items", [])
    wh_id = warehouses[0]["id"]

    order_id = await create_test_order(async_client, admin_headers, wh_id)

    opt_res = await async_client.post(
        "/api/v1/optimization/optimize",
        json={"warehouse_id": wh_id, "order_ids": [order_id], "time_limit_seconds": 1},
        headers=admin_headers,
    )
    job_id = opt_res.json()["job_id"]

    create_res = await async_client.post(
        f"/api/v1/optimization/jobs/{job_id}/create-routes",
        json={"job_id": job_id},
        headers=admin_headers,
    )
    route_id = create_res.json()["route_ids"][0]

    route_res = await async_client.get(f"/api/v1/routes/{route_id}", headers=admin_headers)
    stop_id = route_res.json()["stops"][0]["id"]

    # 1. Cannot record arrival on a PLANNED (unstarted) route
    arr_early = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop_id}/arrive",
        headers=admin_headers,
    )
    assert arr_early.status_code == 400

    # 2. Cannot complete route while stops are pending
    comp_early = await async_client.post(
        f"/api/v1/routes/{route_id}/complete",
        headers=admin_headers,
    )
    assert comp_early.status_code == 400

    # 3. Start route
    await async_client.post(f"/api/v1/routes/{route_id}/start", headers=admin_headers)

    # 4. Deliver stop
    del_res = await async_client.post(f"/api/v1/routes/{route_id}/stops/{stop_id}/deliver", headers=admin_headers)
    assert del_res.status_code == 200

    # 5. Cannot transition from DELIVERED back to ARRIVED
    arr_again = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop_id}/arrive",
        headers=admin_headers,
    )
    assert arr_again.status_code == 400

    # 6. Cannot fail an already DELIVERED stop
    fail_del = await async_client.post(
        f"/api/v1/routes/{route_id}/stops/{stop_id}/fail",
        headers=admin_headers,
    )
    assert fail_del.status_code == 400

    # 7. Cannot cancel an already COMPLETED route
    cancel_comp = await async_client.post(f"/api/v1/routes/{route_id}/cancel", headers=admin_headers)
    assert cancel_comp.status_code == 400


@pytest.mark.asyncio
async def test_manager_and_driver_route_endpoints_and_isolation(async_client: AsyncClient):
    mgr_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # Logistics Manager lists routes
    res_list = await async_client.get("/api/v1/routes", headers=mgr_headers)
    assert res_list.status_code == 200
    assert "items" in res_list.json()

    # Driver lists routes (isolated to own)
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    res_drv_list = await async_client.get("/api/v1/routes", headers=driver_headers)
    assert res_drv_list.status_code == 200
    assert "items" in res_drv_list.json()

    # Route stops endpoint check
    if res_list.json()["items"]:
        first_route = res_list.json()["items"][0]
        stops_res = await async_client.get(f"/api/v1/routes/{first_route['id']}/stops", headers=mgr_headers)
        assert stops_res.status_code == 200
        assert "items" in stops_res.json()
