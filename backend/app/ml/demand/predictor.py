import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd

from app.ml.demand.dataset import get_historical_demand_dataset
from app.ml.demand.features import extract_features_for_forecast_date, FEATURE_COLUMNS
from app.ml.demand.trainer import (
    MODEL_PATH,
    METADATA_PATH,
    MODEL_VERSION,
    train_demand_forecasting_model,
)

logger = logging.getLogger(__name__)


class DemandForecastService:
    """
    Production AI Demand Forecasting Service with Recursive Horizon Inference
    and Deterministic Moving-Average Fallback.
    """

    def __init__(self):
        self._model = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._load_model_artifacts()

    def _load_model_artifacts(self):
        """Loads trained model pipeline and metadata, or trains baseline if missing."""
        try:
            if MODEL_PATH.exists() and METADATA_PATH.exists():
                self._model = joblib.load(MODEL_PATH)
                with open(METADATA_PATH, "r") as f:
                    self._metadata = json.load(f)
                logger.info(f"Loaded Demand Forecast model: {self._metadata.get('selected_model')} ({self._metadata.get('model_version')})")
            else:
                logger.info("Initializing baseline Demand Forecasting model artifact...")
                self._metadata = train_demand_forecasting_model()
                self._model = joblib.load(MODEL_PATH)
        except Exception as e:
            logger.warning(f"Could not load Demand Forecasting model ({e}). Fallback mode active.")
            self._model = None
            self._metadata = None

    def reload(self):
        """Reloads artifacts after retraining."""
        self._load_model_artifacts()

    def get_metadata(self) -> Dict[str, Any]:
        """Returns active model metadata."""
        if not self._metadata and METADATA_PATH.exists():
            try:
                with open(METADATA_PATH, "r") as f:
                    self._metadata = json.load(f)
            except Exception:
                pass

        if self._metadata:
            return self._metadata

        return {
            "model_version": "fallback-v1",
            "selected_model": "Deterministic 7-Day Moving Average Fallback",
            "trained_at": None,
            "training_samples": 0,
            "status": "FALLBACK_ACTIVE",
            "selected_metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
        }

    def forecast_demand(
        self,
        horizon: int = 7,
        warehouse_id: Optional[str] = None,
        custom_series: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Forecasts daily order demand for the specified horizon (7, 14, or 30 days).
        Uses Machine Learning recursive step forecasting with uncertainty intervals,
        or deterministic moving average fallback.
        """
        # Validate horizon bounds
        if horizon not in [7, 14, 30]:
            if horizon <= 0 or horizon > 60:
                raise ValueError("Invalid forecast horizon. Supported horizons: 7, 14, or 30 days.")

        records = custom_series if custom_series is not None else get_historical_demand_dataset(warehouse_id=warehouse_id)

        if not records or len(records) < 7:
            # Insufficient data fallback
            return self._generate_fallback_forecast(
                horizon=horizon,
                warehouse_id=warehouse_id,
                reason="INSUFFICIENT_HISTORICAL_DATA",
                base_demand=35,
            )

        # 1. Attempt Machine Learning Recursive Forecasting
        if self._model is not None:
            try:
                historical_counts = [float(r["orders_count"]) for r in records]
                last_date_str = records[-1]["date"]
                last_date = datetime.fromisoformat(last_date_str).date()

                res_std = float(self._metadata.get("residual_std", 3.2)) if self._metadata else 3.2
                simulated_series = list(historical_counts)
                forecast_items: List[Dict[str, Any]] = []

                for step in range(1, horizon + 1):
                    target_d = last_date + timedelta(days=step)
                    feat_dict = extract_features_for_forecast_date(target_d, simulated_series)
                    feat_df = pd.DataFrame([feat_dict])[FEATURE_COLUMNS]

                    pred_val = float(self._model.predict(feat_df)[0])
                    # Ensure positive predicted orders
                    pred_orders = max(1, int(round(pred_val)))

                    # Prediction interval (~95% confidence bounds)
                    lower_bound = max(0, int(round(pred_val - 1.96 * res_std)))
                    upper_bound = int(round(pred_val + 1.96 * res_std))

                    forecast_items.append({
                        "date": target_d.isoformat(),
                        "predicted_orders": pred_orders,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                    })

                    # Feed forward predicted value for recursive multi-step lag/rolling calculations
                    simulated_series.append(float(pred_orders))

                return {
                    "forecast": forecast_items,
                    "model_version": self._metadata.get("model_version", MODEL_VERSION) if self._metadata else MODEL_VERSION,
                    "selected_model": self._metadata.get("selected_model", "RandomForestRegressor") if self._metadata else "RandomForestRegressor",
                    "source": "ML",
                    "horizon_days": horizon,
                    "warehouse_id": warehouse_id,
                }
            except Exception as e:
                logger.warning(f"ML forecast failed ({e}). Falling back to deterministic moving average.")

        # 2. Deterministic Fallback (7-Day Moving Average with weekend adjustments)
        recent_counts = [float(r["orders_count"]) for r in records[-14:]]
        base_avg = float(np.mean(recent_counts)) if recent_counts else 40.0
        return self._generate_fallback_forecast(
            horizon=horizon,
            warehouse_id=warehouse_id,
            reason="MODEL_UNAVAILABLE",
            base_demand=base_avg,
        )

    def _generate_fallback_forecast(
        self,
        horizon: int,
        warehouse_id: Optional[str],
        reason: str,
        base_demand: float,
    ) -> Dict[str, Any]:
        """Generates deterministic moving average forecast items."""
        start_date = date.today()
        forecast_items: List[Dict[str, Any]] = []

        for step in range(1, horizon + 1):
            target_d = start_date + timedelta(days=step)
            dow = target_d.weekday()
            dow_multiplier = 0.65 if dow in [5, 6] else 1.15
            pred_orders = max(1, int(round(base_demand * dow_multiplier)))

            forecast_items.append({
                "date": target_d.isoformat(),
                "predicted_orders": pred_orders,
                "lower_bound": max(0, int(round(pred_orders * 0.8))),
                "upper_bound": int(round(pred_orders * 1.25)),
            })

        return {
            "forecast": forecast_items,
            "model_version": "fallback-v1",
            "selected_model": "Deterministic 7-Day Moving Average Fallback",
            "source": "FALLBACK",
            "reason": reason,
            "horizon_days": horizon,
            "warehouse_id": warehouse_id,
        }


demand_forecast_service = DemandForecastService()
