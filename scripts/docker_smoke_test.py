"""
End-to-End Smoke Test against Running Docker Stack
Target: http://localhost:8000
"""
import sys
import time
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"

def run_tests():
    print("=" * 66)
    print("🚀 RUNNING SMOKE TEST AGAINST LIVE DOCKER STACK (http://localhost:8000)")
    print("=" * 66)

    # 1. Healthcheck
    print("\n[1/6] Probing System Health...")
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Healthcheck failed: {r.text}"
    health = r.json()
    print(f"  ✓ System Status: {health['status']}")
    print(f"  ✓ PostgreSQL: {health['services']['database']['status']} ({health['services']['database']['details']})")
    print(f"  ✓ Redis: {health['services']['redis']['status']} ({health['services']['redis']['details']})")

    # 2. Authenticate across all three roles
    print("\n[2/6] Authenticating as ADMIN, LOGISTICS_MANAGER, and DRIVER...")
    roles = [
        ("admin@example.com", "Admin@123456", "ADMIN"),
        ("manager@example.com", "Manager@123456", "LOGISTICS_MANAGER"),
        ("driver@example.com", "Driver@123456", "DRIVER"),
    ]
    tokens = {}
    for email, pwd, expected_role in roles:
        res = httpx.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": email, "password": pwd}
        )
        assert res.status_code == 200, f"Login failed for {email}: {res.text}"
        data = res.json()
        assert data["user"]["role"] == expected_role
        tokens[expected_role] = data["access_token"]
        print(f"  ✓ {expected_role} login successful ({email}).")

    admin_headers = {"Authorization": f"Bearer {tokens['ADMIN']}"}
    mgr_headers = {"Authorization": f"Bearer {tokens['LOGISTICS_MANAGER']}"}
    drv_headers = {"Authorization": f"Bearer {tokens['DRIVER']}"}

    # 3. Order Lifecycle
    print("\n[3/6] Testing Order Management Lifecycle (List, Create, Update)...")
    res_orders = httpx.get(f"{BASE_URL}/api/v1/orders", headers=mgr_headers)
    assert res_orders.status_code == 200, f"List orders failed: {res_orders.text}"
    initial_count = res_orders.json()["total"]
    print(f"  ✓ Initial order count in PostgreSQL: {initial_count}")

    # Fetch customer & warehouse for FK
    res_cust = httpx.get(f"{BASE_URL}/api/v1/customers", headers=mgr_headers)
    cust_data = res_cust.json()
    customer_id = cust_data[0]["id"] if isinstance(cust_data, list) else cust_data["items"][0]["id"]

    res_wh = httpx.get(f"{BASE_URL}/api/v1/warehouses", headers=mgr_headers)
    wh_data = res_wh.json()
    warehouse_id = wh_data[0]["id"] if isinstance(wh_data, list) else wh_data["items"][0]["id"]

    order_payload = {
        "order_number": f"ORD-DOCKER-{int(time.time())}",
        "customer_id": customer_id,
        "warehouse_id": warehouse_id,
        "pickup_address": "123 Main St, New York, NY 10001",
        "pickup_latitude": 40.7128,
        "pickup_longitude": -74.0060,
        "delivery_address": "450 W 33rd St, New York, NY 10001",
        "delivery_latitude": 40.7533,
        "delivery_longitude": -73.9998,
        "package_weight": 18.75,
        "package_dimensions": "30x25x20",
        "priority": "HIGH",
        "special_instructions": "Docker stack verification order"
    }
    res_create = httpx.post(f"{BASE_URL}/api/v1/orders", json=order_payload, headers=mgr_headers)
    assert res_create.status_code == 201, f"Create order failed: {res_create.text}"
    created_order = res_create.json()
    order_id = created_order["id"]
    print(f"  ✓ Created order {order_id} ({created_order['order_number']}) with weight {created_order['package_weight']}kg.")

    # Update order
    res_update = httpx.put(
        f"{BASE_URL}/api/v1/orders/{order_id}",
        json={"status": "ASSIGNED", "priority": "URGENT"},
        headers=mgr_headers
    )
    assert res_update.status_code == 200, f"Update order failed: {res_update.text}"
    updated = res_update.json()
    print(f"  ✓ Updated order {order_id} status to '{updated['status']}' and priority to '{updated['priority']}'.")

    # 4. Route Optimization
    print("\n[4/6] Executing Google OR-Tools Route Optimization in Docker...")
    res_all_orders = httpx.get(f"{BASE_URL}/api/v1/orders", headers=mgr_headers)
    all_order_ids = [o["id"] for o in res_all_orders.json()["items"]][:4]

    opt_payload = {
        "warehouse_id": warehouse_id,
        "order_ids": all_order_ids if order_id in all_order_ids else [order_id] + all_order_ids[:2],
    }
    res_opt = httpx.post(f"{BASE_URL}/api/v1/optimization/optimize", json=opt_payload, headers=mgr_headers, timeout=30.0)
    assert res_opt.status_code == 200, f"Route optimization failed: {res_opt.text}"
    opt_data = res_opt.json()
    print(f"  ✓ OR-Tools VRP Optimization solved: status='{opt_data['status']}', distance={opt_data['total_distance_km']}km, routes={len(opt_data['routes'])}.")

    # 5. AI Decision Intelligence
    print("\n[5/6] Querying AI Operations Summary & Explainable Priority...")
    res_summary = httpx.get(f"{BASE_URL}/api/v1/ai/operations-summary", headers=mgr_headers, timeout=20.0)
    assert res_summary.status_code == 200
    res_priority = httpx.get(f"{BASE_URL}/api/v1/ai/order-priority/{order_id}", headers=mgr_headers, timeout=20.0)
    assert res_priority.status_code == 200
    p_data = res_priority.json()
    print(f"  ✓ Explainable AI Priority Score: {p_data['score']}/100, Tier='{p_data['priority']}', Model='{p_data['model_name']}'.")

    # 6. Audit Trail
    print("\n[6/6] Checking PostgreSQL Audit Trail...")
    res_audit = httpx.get(f"{BASE_URL}/api/v1/audit-logs?limit=20", headers=admin_headers)
    assert res_audit.status_code == 200
    audit_entries = res_audit.json()["items"]
    print(f"  ✓ Security Audit Trail verified: Found {len(audit_entries)} recent audit entries.")

    print("\n" + "=" * 66)
    print(f"🎉 ALL DOCKER SMOKE TESTS PASSED! Target Order ID: {order_id}")
    print("=" * 66)
    return order_id

if __name__ == "__main__":
    run_tests()
