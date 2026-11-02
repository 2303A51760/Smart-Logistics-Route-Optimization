import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_demand_forecast_valid_horizons(async_client: AsyncClient, manager_token_headers: dict):
    for h in [1, 7, 14, 30]:
        res = await async_client.get(f"/api/v1/ai/demand-forecast?horizon={h}", headers=manager_token_headers)
        assert res.status_code == 200
        data = res.json()
        assert "forecast" in data
        assert "horizon_days" in data
        assert data["horizon_days"] == h
        assert len(data["forecast"]) == h


@pytest.mark.asyncio
async def test_ai_demand_forecast_invalid_horizon(async_client: AsyncClient, manager_token_headers: dict):
    res = await async_client.get("/api/v1/ai/demand-forecast?horizon=45", headers=manager_token_headers)
    assert res.status_code == 400
    assert "Allowed forecast horizons" in res.json()["detail"]
