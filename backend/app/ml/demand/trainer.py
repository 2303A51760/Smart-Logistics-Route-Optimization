import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.ml.demand.dataset import get_historical_demand_dataset
from app.ml.demand.features import (
    build_time_series_feature_matrix,
    FEATURE_COLUMNS,
)

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "demand_model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "demand_metadata.json"
MODEL_VERSION = "demand-v1"


def compute_safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes MAPE while guarding against division by zero."""
    denom = np.maximum(1.0, np.abs(y_true))
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def evaluate_forecast_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes MAE, RMSE, and safe MAPE."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = compute_safe_mape(y_true, y_pred)

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }


def train_demand_forecasting_model(
    custom_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Executes chronological time-series model training, baseline benchmarking,
    metric evaluation, and model artifact persistence.
    """
    records = custom_records if custom_records is not None else get_historical_demand_dataset()

    # 1. Feature Engineering
    X_df, y_arr, full_df = build_time_series_feature_matrix(records)

    # 2. Chronological Split (80% Train, 20% Validation - NO Shuffling)
    split_idx = max(int(len(X_df) * 0.8), len(X_df) - 10)
    X_train, X_val = X_df.iloc[:split_idx], X_df.iloc[split_idx:]
    y_train, y_val = y_arr[:split_idx], y_arr[split_idx:]

    # 3. Baseline 1: Naive Persistence (Lag 1 / Lag 7)
    naive_preds = X_val["lag_7"].values
    naive_metrics = evaluate_forecast_predictions(y_val, naive_preds)

    # 4. Baseline 2: 7-Day Moving Average
    ma_preds = X_val["rolling_mean_7"].values
    ma_metrics = evaluate_forecast_predictions(y_val, ma_preds)

    # 5. Advanced Model 1: Random Forest Regressor
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_val)
    rf_metrics = evaluate_forecast_predictions(y_val, rf_preds)

    # 6. Advanced Model 2: Gradient Boosting Regressor
    gb_model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    gb_model.fit(X_train, y_train)
    gb_preds = gb_model.predict(X_val)
    gb_metrics = evaluate_forecast_predictions(y_val, gb_preds)

    # 7. Best Model Selection (lowest validation MAE)
    models_pool = {
        "RandomForestRegressor": (rf_model, rf_metrics),
        "GradientBoostingRegressor": (gb_model, gb_metrics),
    }

    best_name = "RandomForestRegressor"
    best_metrics = rf_metrics
    best_model = rf_model

    if gb_metrics["mae"] < rf_metrics["mae"]:
        best_name = "GradientBoostingRegressor"
        best_metrics = gb_metrics
        best_model = gb_model

    # Retrain selected model on full dataset
    best_model.fit(X_df, y_arr)

    # 8. Compute residual standard deviation for prediction intervals
    residuals = y_arr - best_model.predict(X_df)
    residual_std = float(np.std(residuals))

    # 9. Save Artifacts
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)

    metadata: Dict[str, Any] = {
        "model_version": MODEL_VERSION,
        "selected_model": best_name,
        "trained_at": datetime.utcnow().isoformat(),
        "training_samples": len(records),
        "features": FEATURE_COLUMNS,
        "residual_std": round(residual_std, 2),
        "selected_metrics": best_metrics,
        "models_evaluated": {
            "NaiveBaseline": naive_metrics,
            "MovingAverage7D": ma_metrics,
            "RandomForestRegressor": rf_metrics,
            "GradientBoostingRegressor": gb_metrics,
        },
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Demand Forecasting Model {best_name} ({MODEL_VERSION}) saved with MAE: {best_metrics['mae']:.2f}")
    return metadata
