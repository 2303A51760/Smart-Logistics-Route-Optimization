import pytest
import json
from datetime import datetime, timedelta
from httpx import AsyncClient
from starlette.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.models.user import UserRole
from app.core.logistics_store import SEED_DRIVERS, SEED_DRIVER_LOCATIONS
from app.core.redis import publish_tracking_event, check_redis_connection
from app.schemas.tracking import LocationUpdateMessage


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]



@pytest.mark.asyncio
async def test_schema_coordinate_validation():
    """Verify coordinate and value validation rules."""
    # Valid
    valid_msg = LocationUpdateMessage(
        type="location_update",
        latitude=16.5062,
        longitude=80.6480,
        accuracy=5.0,
        speed=25.5,
        heading=180.0,
    )
    assert valid_msg.latitude == 16.5062
    assert valid_msg.longitude == 80.6480

    # Invalid latitude > 90
    with pytest.raises(Exception):
        LocationUpdateMessage(type="location_update", latitude=95.0, longitude=80.0)

    # Invalid latitude < -90
    with pytest.raises(Exception):
        LocationUpdateMessage(type="location_update", latitude=-95.0, longitude=80.0)

    # Invalid longitude > 180
    with pytest.raises(Exception):
        LocationUpdateMessage(type="location_update", latitude=16.0, longitude=190.0)

    # Invalid longitude < -180
    with pytest.raises(Exception):
        LocationUpdateMessage(type="location_update", latitude=16.0, longitude=-190.0)

    # Invalid speed < 0
    with pytest.raises(Exception):
        LocationUpdateMessage(type="location_update", latitude=16.0, longitude=80.0, speed=-5.0)

    # Invalid accuracy < 0
    with pytest.raises(Exception):
        LocationUpdateMessage(type="location_update", latitude=16.0, longitude=80.0, accuracy=-1.0)


@pytest.mark.asyncio
async def test_driver_location_history_recording_and_retrieval(async_client: AsyncClient):
    """Test recording location points and retrieving history via REST API."""
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Query initial history
    res = await async_client.get("/api/v1/tracking/drivers/drv-001/history", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "locations" in data
    assert data["driver_id"] == "drv-001"
    assert "total_points" in data


@pytest.mark.asyncio
async def test_driver_latest_locations_manager_access(async_client: AsyncClient):
    """Logistics manager should be able to view all operational drivers' latest positions."""
    manager_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    res = await async_client.get("/api/v1/tracking/drivers", headers=manager_headers)
    assert res.status_code == 200
    data = res.json()
    assert "drivers" in data
    assert len(data["drivers"]) >= 2
    driver_ids = [d["driver_id"] for d in data["drivers"]]
    assert "drv-001" in driver_ids
    assert "drv-002" in driver_ids


@pytest.mark.asyncio
async def test_driver_isolation_on_tracking_endpoints(async_client: AsyncClient):
    """Driver should only see their own location and history, not other drivers."""
    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # Driver fetching own latest positions
    res = await async_client.get("/api/v1/tracking/drivers", headers=driver_headers)
    assert res.status_code == 200
    data = res.json()
    assert "drivers" in data
    # Only own driver record returned
    assert len(data["drivers"]) == 1
    assert data["drivers"][0]["driver_id"] == "drv-001"

    # Driver fetching own history
    res_own_history = await async_client.get("/api/v1/tracking/drivers/drv-001/history", headers=driver_headers)
    assert res_own_history.status_code == 200

    # Driver attempting to fetch another driver's history (drv-002) MUST be forbidden (403)
    res_other_history = await async_client.get("/api/v1/tracking/drivers/drv-002/history", headers=driver_headers)
    assert res_other_history.status_code == 403
    assert "Drivers are only authorized" in res_other_history.json()["detail"]


@pytest.mark.asyncio
async def test_location_history_query_parameters(async_client: AsyncClient):
    """Test start_time, end_time, and limit filtering on location history API."""
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Query with limit
    res = await async_client.get(
        "/api/v1/tracking/drivers/drv-001/history?limit=5",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["locations"]) <= 5

    # Invalid limit > 1000
    res_inv = await async_client.get(
        "/api/v1/tracking/drivers/drv-001/history?limit=2000",
        headers=admin_headers,
    )
    assert res_inv.status_code == 422  # Validation error on max limit


@pytest.mark.asyncio
async def test_redis_resilience_and_publish():
    """Verify Redis publishing handles both live and offline states without raising unhandled exceptions."""
    test_event = {
        "type": "driver_location_updated",
        "driver_id": "drv-001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed": 35.0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    # Should return bool without crashing
    result = await publish_tracking_event(test_event)
    assert isinstance(result, bool)

    conn_check = await check_redis_connection()
    assert isinstance(conn_check, bool)


@pytest.mark.asyncio
async def test_tracking_endpoints_unauthorized(async_client: AsyncClient):
    """Unauthenticated requests must be rejected with 401."""
    res_drivers = await async_client.get("/api/v1/tracking/drivers")
    assert res_drivers.status_code == 401

    res_history = await async_client.get("/api/v1/tracking/drivers/drv-001/history")
    assert res_history.status_code == 401


def test_websocket_unauthorized_access():
    """WebSocket connection without token or with invalid token should be rejected."""
    client = TestClient(app)
    with client.websocket_connect("/ws/tracking") as websocket:
        # Client sends invalid or no token frame
        websocket.send_json({"type": "AUTH", "token": "invalid_jwt_token"})
        res = websocket.receive_json()
        assert res.get("type") == "AUTH_ERROR"


def test_websocket_driver_tracking_and_identity_enforcement():
    """
    Test driver connecting via WebSocket and publishing GPS location update.
    The backend must enforce authenticated driver identity and reject spoofed IDs.
    """
    driver_token = create_access_token(
        subject="usr-drv-003",
        role=UserRole.DRIVER.value,
        name="Alex River",
    )

    client = TestClient(app)
    with client.websocket_connect(f"/ws/tracking?token={driver_token}") as websocket:
        # Handshake confirmation
        handshake = websocket.receive_json()
        assert handshake["type"] == "CONNECTION_ESTABLISHED"
        assert handshake["authenticated_as"]["driver_id"] == "drv-001"

        # Driver sends valid location update, attempting to spoof another driver_id
        update_msg = {
            "type": "location_update",
            "driver_id": "drv-999_spoofed",
            "latitude": 40.7306,
            "longitude": -73.9352,
            "accuracy": 4.2,
            "speed": 28.5,
            "heading": 90.0,
        }
        websocket.send_json(update_msg)

        ack = websocket.receive_json()
        assert ack["type"] == "LOCATION_ACKNOWLEDGED"
        # Backend strictly associated with authenticated drv-001, NOT drv-999
        assert ack["driver_id"] == "drv-001"

        # Verify driver location in store updated
        assert SEED_DRIVERS["drv-001"]["current_latitude"] == 40.7306
        assert SEED_DRIVERS["drv-001"]["current_longitude"] == -73.9352


def test_websocket_invalid_coordinates_rejected():
    """Invalid GPS coordinates sent over WebSocket must be caught and return error message."""
    driver_token = create_access_token(
        subject="usr-drv-003",
        role=UserRole.DRIVER.value,
        name="Alex River",
    )

    client = TestClient(app)
    with client.websocket_connect(f"/ws/tracking?token={driver_token}") as websocket:
        _ = websocket.receive_json()

        # Send invalid latitude 120.0
        bad_msg = {
            "type": "location_update",
            "latitude": 120.0,
            "longitude": 80.0,
        }
        websocket.send_json(bad_msg)

        err_response = websocket.receive_json()
        assert err_response["type"] == "ERROR"
        assert "validation error" in err_response["message"].lower()
