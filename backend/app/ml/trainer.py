import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.ml.dataset import get_historical_dataset
from app.ml.features import (
    create_feature_preprocessor,
    records_to_feature_matrix,
    ALL_FEATURE_COLUMNS,
)

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "eta_model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "eta_metadata.json"
MODEL_VERSION = "eta-v1"


def evaluate_model(
    name: str,
    pipeline: Pipeline,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
) -> Dict[str, float]:
    """Computes MAE, RMSE, and R2 evaluation metrics."""
    preds = pipeline.predict(X_val)
    mae = float(mean_absolute_error(y_val, preds))
    rmse = float(np.sqrt(mean_squared_error(y_val, preds)))
    r2 = float(r2_score(y_val, preds))

    logger.info(f"[{name}] Evaluation -> MAE: {mae:.2f} min, RMSE: {rmse:.2f} min, R2: {r2:.3f}")
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 3),
    }


def train_eta_model(custom_records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Executes the end-to-end model training, evaluation, selection, and artifact persistence.
    """
    records = custom_records if custom_records is not None else get_historical_dataset()

    if len(records) < 5:
        raise ValueError(f"Insufficient training records ({len(records)} found, minimum 5 required).")

    # 1. Feature extraction
    X_dicts, y_arr = records_to_feature_matrix(records)
    df_X = pd.DataFrame(X_dicts)

    # 2. Chronological Train / Validation Split (80% Train, 20% Validation)
    split_idx = max(int(len(records) * 0.8), len(records) - 4)
    X_train, X_val = df_X.iloc[:split_idx], df_X.iloc[split_idx:]
    y_train, y_val = y_arr[:split_idx], y_arr[split_idx:]

    # 3. Model 1: Linear Regression (Baseline)
    lr_pipeline = Pipeline([
        ("preprocessor", create_feature_preprocessor()),
        ("regressor", LinearRegression()),
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_metrics = evaluate_model("LinearRegression", lr_pipeline, X_val, y_val)

    # 4. Model 2: Random Forest Regressor (Advanced)
    rf_pipeline = Pipeline([
        ("preprocessor", create_feature_preprocessor()),
        ("regressor", RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)),
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_metrics = evaluate_model("RandomForestRegressor", rf_pipeline, X_val, y_val)

    # 5. Model Selection: Select based on lowest Validation MAE
    if rf_metrics["mae"] <= lr_metrics["mae"]:
        selected_name = "RandomForestRegressor"
        best_pipeline = rf_pipeline
        selected_metrics = rf_metrics
    else:
        selected_name = "LinearRegression"
        best_pipeline = lr_pipeline
        selected_metrics = lr_metrics

    # Retrain selected pipeline on full dataset for maximum production accuracy
    best_pipeline.fit(df_X, y_arr)

    # 6. Save Artifacts
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)

    metadata: Dict[str, Any] = {
        "model_version": MODEL_VERSION,
        "selected_model": selected_name,
        "trained_at": datetime.utcnow().isoformat(),
        "training_samples": len(records),
        "features": ALL_FEATURE_COLUMNS,
        "selected_metrics": selected_metrics,
        "models_evaluated": {
            "LinearRegression": lr_metrics,
            "RandomForestRegressor": rf_metrics,
        },
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model {selected_name} ({MODEL_VERSION}) successfully saved to {MODEL_PATH}")
    return metadata
