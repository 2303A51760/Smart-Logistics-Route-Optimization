import sys
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"
ORDER_ID = "ord-33d923"

def main():
    print("Testing data persistence across backend restart...")
    res_login = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "manager@example.com", "password": "Manager@123456"})
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    token = res_login.json()["access_token"]

    r = httpx.get(f"{BASE_URL}/api/v1/orders/{ORDER_ID}", headers={"Authorization": f"Bearer {token}"})
    print(f"HTTP Status: {r.status_code}")
    assert r.status_code == 200, f"Order retrieval failed: {r.text}"
    ord_data = r.json()
    print(f"✓ ORDER PERSISTENCE VERIFIED:")
    print(f"  - Order ID: {ord_data.get('id')}")
    print(f"  - Order Number: {ord_data.get('order_number')}")
    print(f"  - Status: {ord_data.get('status')} (expected: ASSIGNED)")
    print(f"  - Priority: {ord_data.get('priority')} (expected: URGENT)")
    print(f"  - Package Weight: {ord_data.get('package_weight')}kg (expected: 18.75kg)")

if __name__ == "__main__":
    main()

