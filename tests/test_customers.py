import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, role_password: str = "Admin@123456") -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": role_password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_customer_crud_lifecycle(async_client: AsyncClient):
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Create customer
    create_payload = {
        "name": "Hudson Yards Groceries",
        "phone": "+1-212-555-0922",
        "email": "procurement@hudsonyards.com",
        "address": "20 Hudson Yards, New York, NY",
        "latitude": 40.7538,
        "longitude": -74.0022,
    }
    create_res = await async_client.post("/api/v1/customers", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    cust_data = create_res.json()
    cust_id = cust_data["id"]
    assert cust_data["name"] == "Hudson Yards Groceries"

    # Get customer
    get_res = await async_client.get(f"/api/v1/customers/{cust_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["phone"] == "+1-212-555-0922"

    # Update customer
    update_payload = {"phone": "+1-212-555-1122", "name": "Hudson Yards Retail Mart"}
    put_res = await async_client.put(f"/api/v1/customers/{cust_id}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["phone"] == "+1-212-555-1122"
    assert put_res.json()["name"] == "Hudson Yards Retail Mart"

    # Delete customer
    del_res = await async_client.delete(f"/api/v1/customers/{cust_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_customer_invalid_email_and_coordinates(async_client: AsyncClient):
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid email format
    bad_email = {
        "name": "Bad Email Corp",
        "phone": "+1-555-0000",
        "email": "not-an-email",
        "address": "123 Main St",
        "latitude": 40.0,
        "longitude": -74.0,
    }
    res1 = await async_client.post("/api/v1/customers", json=bad_email, headers=headers)
    assert res1.status_code == 422
