import pytest
from httpx import AsyncClient
from app.ml.demand.dataset import (
    fill_missing_dates,
    aggregate_orders_by_period,
    get_historical_demand_dataset,
)
from app.ml.demand.features import (
    build_time_series_feature_matrix,
    FEATURE_COLUMNS,
)
from app.ml.demand.trainer import (
    train_demand_forecasting_model,
    MODEL_VERSION,
)
from app.ml.demand.predictor import DemandForecastService
from app.ml.demand.capacity import CapacityPlanningService


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_fill_missing_dates_preserves_zero_demand():
    """Verify missing dates are zero-filled rather than silently dropped."""
    sparse_records = [
        {"date": "2026-08-01", "orders_count": 40},
        # 2026-08-02 is missing
        {"date": "2026-08-03", "orders_count": 35},
    ]
    filled = fill_missing_dates(sparse_records)
    assert len(filled) == 3
    assert filled[0]["date"] == "2026-08-01" and filled[0]["orders_count"] == 40
    assert filled[1]["date"] == "2026-08-02" and filled[1]["orders_count"] == 0
    assert filled[2]["date"] == "2026-08-03" and filled[2]["orders_count"] == 35


def test_aggregate_orders_by_daily_and_weekly():
    """Verify daily and weekly aggregation of order events."""
    raw_orders = [
        {"created_at": "2026-08-01T10:00:00Z", "warehouse_id": "wh-001"},
        {"created_at": "2026-08-01T14:30:00Z", "warehouse_id": "wh-001"},
        {"created_at": "2026-08-02T09:15:00Z", "warehouse_id": "wh-001"},
    ]
    daily = aggregate_orders_by_period(raw_orders, period="daily")
    assert len(daily) == 2
    assert daily[0]["orders_count"] == 2
    assert daily[1]["orders_count"] == 1


def test_time_series_features_and_no_data_leakage():
    """Verify feature engineering produces shifted lag & rolling features with zero leakage."""
    dataset = get_historical_demand_dataset()
    X_df, y_arr, full_df = build_time_series_feature_matrix(dataset)

    assert len(X_df) == len(y_arr)
    for col in FEATURE_COLUMNS:
        assert col in X_df.columns

    # Verify lag_1 is strictly previous day's orders
    row_idx = 5
    expected_prev = full_df.iloc[row_idx - 1]["orders_count"]
    actual_lag_1 = X_df.iloc[row_idx]["lag_1"]
    assert actual_lag_1 == expected_prev


def test_model_training_and_chronological_evaluation():
    """Verify chronological training, baseline benchmarking, and artifact creation."""
    meta = train_demand_forecasting_model()
    assert meta["model_version"] == MODEL_VERSION
    assert "selected_metrics" in meta
    assert "mae" in meta["selected_metrics"]
    assert "rmse" in meta["selected_metrics"]
    assert "mape" in meta["selected_metrics"]
    assert "models_evaluated" in meta
    assert "NaiveBaseline" in meta["models_evaluated"]
    assert "MovingAverage7D" in meta["models_evaluated"]
    assert "RandomForestRegressor" in meta["models_evaluated"]


def test_demand_forecast_service_horizons():
    """Verify 7, 14, and 30 day recursive forecast generation with valid prediction intervals."""
    svc = DemandForecastService()
    for horizon in [7, 14, 30]:
        res = svc.forecast_demand(horizon=horizon)
        assert res["source"] == "ML"
        assert len(res["forecast"]) == horizon
        for item in res["forecast"]:
            assert "date" in item
            assert item["predicted_orders"] > 0
            assert item["lower_bound"] <= item["predicted_orders"]
            assert item["upper_bound"] >= item["predicted_orders"]


def test_demand_forecast_service_fallback_mode():
    """Verify deterministic moving average fallback when model is unavailable or records are missing."""
    svc = DemandForecastService()
    svc._model = None  # Force fallback
    res = svc.forecast_demand(horizon=7)
    assert res["source"] == "FALLBACK"
    assert len(res["forecast"]) == 7
    assert "reason" in res


def test_capacity_planning_calculations():
    """Verify fleet utilization percentage, capacity gap, and driver requirement."""
    forecast_mock = {
        "horizon_days": 7,
        "forecast": [{"predicted_orders": 50} for _ in range(7)],  # Total = 350
        "warehouse_id": "wh-001",
    }
    # 2 drivers * 25 orders/day * 7 days = 350 capacity -> 100% utilization
    plan = CapacityPlanningService.calculate_capacity_plan(
        forecast_result=forecast_mock,
        active_drivers=2,
        active_vehicles=2,
    )
    assert plan["forecasted_total_demand"] == 350
    assert plan["available_capacity"] == 350
    assert plan["capacity_utilization_percent"] == 100.0
    assert plan["capacity_gap"] == 0
    assert plan["status"] in ["OVER_CAPACITY", "HIGH_UTILIZATION"]


@pytest.mark.asyncio
async def test_forecast_demand_api_endpoints(async_client: AsyncClient):
    """Test GET /api/v1/forecast/demand for 7, 14, 30 day horizons and bad horizon rejection."""
    token = await get_auth_token(async_client, "admin@example.com", "Admin@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # 7-day
    res_7 = await async_client.get("/api/v1/forecast/demand?horizon=7", headers=headers)
    assert res_7.status_code == 200
    assert len(res_7.json()["forecast"]) == 7

    # 14-day
    res_14 = await async_client.get("/api/v1/forecast/demand?horizon=14", headers=headers)
    assert res_14.status_code == 200
    assert len(res_14.json()["forecast"]) == 14

    # 30-day
    res_30 = await async_client.get("/api/v1/forecast/demand?horizon=30", headers=headers)
    assert res_30.status_code == 200
    assert len(res_30.json()["forecast"]) == 30

    # Invalid horizon (99) -> 400 Bad Request
    res_bad = await async_client.get("/api/v1/forecast/demand?horizon=99", headers=headers)
    assert res_bad.status_code == 400


@pytest.mark.asyncio
async def test_capacity_planning_api_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/forecast/capacity endpoint."""
    token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/forecast/capacity?horizon=7", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "forecasted_total_demand" in data
    assert "available_capacity" in data
    assert "capacity_utilization_percent" in data
    assert "status" in data
    assert "required_drivers" in data


@pytest.mark.asyncio
async def test_warehouse_comparison_and_rbac(async_client: AsyncClient):
    """Verify warehouse comparison works and Driver is forbidden from analytics/retraining."""
    manager_token = await get_auth_token(async_client, "manager@example.com", "Manager@123456")
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    driver_token = await get_auth_token(async_client, "driver@example.com", "Driver@123456")
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # Warehouse comparison
    res_comp = await async_client.get("/api/v1/forecast/warehouses/comparison?horizon=7", headers=manager_headers)
    assert res_comp.status_code == 200
    assert len(res_comp.json()["warehouses"]) >= 1

    # Manager retrains demand model
    res_retrain = await async_client.post("/api/v1/forecast/demand/retrain", headers=manager_headers)
    assert res_retrain.status_code == 200

    # Driver attempting to access analytics -> 403 Forbidden
    res_drv_ana = await async_client.get("/api/v1/forecast/analytics", headers=driver_headers)
    assert res_drv_ana.status_code == 403

    # Driver attempting to retrain -> 403 Forbidden
    res_drv_ret = await async_client.post("/api/v1/forecast/demand/retrain", headers=driver_headers)
    assert res_drv_ret.status_code == 403
