import pytest
from httpx import AsyncClient
from app.ml.dataset import clean_and_validate_records, haversine_distance
from app.ml.features import (
    extract_feature_dict,
    ALL_FEATURE_COLUMNS,
)
from app.ml.trainer import train_eta_model, MODEL_VERSION
from app.ml.predictor import ETAPredictionService


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_haversine_distance_calculation():
    """Verify great-circle distance calculation between NYC coordinates."""
    # Midtown to Lower Manhattan (~5.2 km)
    dist = haversine_distance(40.7580, -73.9855, 40.7128, -74.0060)
    assert 4.5 <= dist <= 6.0


def test_dataset_cleaning_and_validation():
    """Verify corrupt, negative, or out-of-bound records are cleanly filtered."""
    raw_records = [
        {"distance_km": 10.0, "actual_delivery_duration_minutes": 25.0, "package_weight": 5.0, "number_of_stops": 3, "stop_sequence": 1, "hour": 14, "day_of_week": 2, "priority": "NORMAL", "vehicle_type": "VAN"},
        {"distance_km": -5.0, "actual_delivery_duration_minutes": 20.0},  # Negative distance -> drop
        {"distance_km": 15.0, "actual_delivery_duration_minutes": -10.0},  # Negative duration -> drop
        {"distance_km": 12.0, "actual_delivery_duration_minutes": 30.0, "hour": 29},  # Invalid hour -> drop
    ]
    cleaned = clean_and_validate_records(raw_records)
    assert len(cleaned) == 1
    assert cleaned[0]["distance_km"] == 10.0


def test_feature_engineering_pipeline():
    """Verify feature extractor extracts expected columns without data leakage."""
    rec = {
        "distance_km": 8.4,
        "package_weight": 12.0,
        "priority": "HIGH",
        "vehicle_type": "TRUCK",
        "number_of_stops": 4,
        "stop_sequence": 2,
        "hour": 15,
        "day_of_week": 3,
        "actual_delivery_duration_minutes": 35.0,  # Target value
    }
    feat_dict = extract_feature_dict(rec)
    # Ensure all required features are present
    for col in ALL_FEATURE_COLUMNS:
        assert col in feat_dict
    # Guarantee no target or post-event actual values leak into features
    assert "actual_delivery_duration_minutes" not in feat_dict
    assert "actual_arrival_time" not in feat_dict


def test_model_training_and_evaluation():
    """Verify training executes, evaluates LinearRegression vs RandomForest, and saves metadata."""
    metadata = train_eta_model()
    assert "model_version" in metadata
    assert metadata["model_version"] == MODEL_VERSION
    assert metadata["selected_model"] in ["RandomForestRegressor", "LinearRegression"]
    assert "selected_metrics" in metadata
    assert "mae" in metadata["selected_metrics"]
    assert "rmse" in metadata["selected_metrics"]
    assert "r2" in metadata["selected_metrics"]
    assert metadata["training_samples"] >= 20


def test_eta_prediction_service_inference():
    """Verify ETAPredictionService produces valid predictions with confidence intervals."""
    svc = ETAPredictionService()
    input_data = {
        "distance_km": 10.5,
        "package_weight": 8.0,
        "priority": "NORMAL",
        "vehicle_type": "VAN",
        "number_of_stops": 4,
        "stop_sequence": 2,
        "hour": 14,
        "day_of_week": 2,
    }
    pred = svc.predict_eta(input_data)
    assert "predicted_duration_minutes" in pred
    assert pred["predicted_duration_minutes"] > 0
    assert "estimated_arrival" in pred
    assert pred["source"] in ["ML", "FALLBACK"]
    assert pred["confidence_interval_min"] <= pred["predicted_duration_minutes"]
    assert pred["confidence_interval_max"] >= pred["predicted_duration_minutes"]


def test_eta_fallback_mode_on_invalid_or_missing_model():
    """Verify deterministic fallback calculations when model pipeline is unavailable."""
    svc = ETAPredictionService()
    svc._pipeline = None  # Force fallback
    input_data = {
        "distance_km": 14.0,
        "number_of_stops": 3,
        "stop_sequence": 2,
    }
    pred = svc.predict_eta(input_data)
    assert pred["source"] == "FALLBACK"
    assert pred["predicted_duration_minutes"] > 0
    assert "estimated_arrival" in pred


@pytest.mark.asyncio
async def test_eta_predict_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/eta/predict endpoint."""
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "distance_km": 12.5,
        "package_weight": 10.0,
        "priority": "HIGH",
        "vehicle_type": "VAN",
        "number_of_stops": 5,
        "stop_sequence": 2,
        "hour": 15,
        "day_of_week": 3,
    }
    res = await async_client.post("/api/v1/eta/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_duration_minutes" in data
    assert data["predicted_duration_minutes"] > 0
    assert "estimated_arrival" in data
    assert data["source"] in ["ML", "FALLBACK"]


@pytest.mark.asyncio
async def test_order_eta_api_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/eta/orders/{order_id} endpoint."""
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    res = await async_client.get("/api/v1/eta/orders/ord-001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_duration_minutes" in data
    assert "estimated_arrival" in data


@pytest.mark.asyncio
async def test_route_cumulative_eta_api_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/eta/routes/{route_id} endpoint."""
    admin_token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    res = await async_client.get("/api/v1/eta/routes/rt-001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_distance_km" in data
    assert "total_predicted_duration_minutes" in data
    assert "stops" in data
    assert len(data["stops"]) >= 2
    for s in data["stops"]:
        assert "predicted_duration_minutes" in s
        assert "estimated_arrival" in s


@pytest.mark.asyncio
async def test_ml_analytics_and_retrain_rbac(async_client: AsyncClient):
    """Verify ADMIN & LOGISTICS_MANAGER can view/retrain models, while DRIVER is forbidden (403)."""
    manager_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # Manager gets analytics
    res_mgr = await async_client.get("/api/v1/eta/analytics", headers=manager_headers)
    assert res_mgr.status_code == 200
    meta = res_mgr.json()
    assert "model_version" in meta
    assert "selected_metrics" in meta

    # Manager triggers retrain
    res_retrain = await async_client.post("/api/v1/eta/retrain", headers=manager_headers)
    assert res_retrain.status_code == 200

    # Driver attempting to access analytics -> 403 Forbidden
    res_drv_analytics = await async_client.get("/api/v1/eta/analytics", headers=driver_headers)
    assert res_drv_analytics.status_code == 403

    # Driver attempting to retrain -> 403 Forbidden
    res_drv_retrain = await async_client.post("/api/v1/eta/retrain", headers=driver_headers)
    assert res_drv_retrain.status_code == 403
