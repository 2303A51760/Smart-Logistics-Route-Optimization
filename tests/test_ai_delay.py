import pytest
from httpx import AsyncClient
from app.ml.delay_prediction import delay_predictor


def test_delay_predictor_logic():
    # 1. High delay risk scenario (heavy rain, heavy traffic, many stops, tight deadline)
    high_risk = delay_predictor.predict_delay_risk(
        order_id="ord-delay-1",
        distance_km=45.0,
        stops_count=8,
        hour_of_day=17,
        weather_factor=3,
        traffic_index=2.2,
        weight_kg=40.0,
        deadline_minutes_remaining=40.0,
    )
    assert high_risk["delay_probability"] >= 0.70
    assert high_risk["risk_level"] in ["HIGH", "CRITICAL"]
    assert high_risk["predicted_delay_minutes"] > 0
    assert len(high_risk["factors"]) > 0

    # 2. Low delay risk scenario (clear weather, low traffic, close distance)
    low_risk = delay_predictor.predict_delay_risk(
        order_id="ord-delay-2",
        distance_km=4.0,
        stops_count=1,
        hour_of_day=10,
        weather_factor=1,
        traffic_index=1.0,
        weight_kg=2.0,
        deadline_minutes_remaining=180.0,
    )
    assert low_risk["delay_probability"] < 0.40
    assert low_risk["risk_level"] == "LOW"


@pytest.mark.asyncio
async def test_delay_risk_api_endpoints(async_client: AsyncClient, admin_token_headers: dict):
    # POST /api/v1/ai/delay-risk
    payload = {
        "order_id": "ord-custom-101",
        "distance_km": 25.0,
        "stops_count": 4,
        "traffic_index": 1.5,
        "weather_factor": 2,
    }
    res = await async_client.post("/api/v1/ai/delay-risk", json=payload, headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["order_id"] == "ord-custom-101"
    assert "delay_probability" in data
    assert "risk_level" in data
    assert "predicted_delay_minutes" in data
    assert "factors" in data
