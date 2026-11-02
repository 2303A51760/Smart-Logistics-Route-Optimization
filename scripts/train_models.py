#!/usr/bin/env python3
"""
Regenerates ML model artifacts:
1. ETA estimation regression model (RandomForest/LinearRegression) -> backend/app/ml/artifacts/eta_model.joblib
2. Demand forecasting time-series model (GradientBoosting/RandomForest) -> backend/app/ml/demand/artifacts/demand_model.joblib
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

from app.ml.trainer import train_eta_model
from app.ml.demand.trainer import train_demand_forecasting_model


def main():
    print("=" * 60)
    print("Training ETA Estimation Model...")
    eta_meta = train_eta_model()
    print(f"ETA Model trained: {eta_meta['selected_model']} (Samples: {eta_meta['training_samples']}, MAE: {eta_meta['selected_metrics']['mae']}m)")

    print("-" * 60)
    print("Training Demand Forecasting Model...")
    demand_meta = train_demand_forecasting_model()
    print(f"Demand Model trained: {demand_meta['selected_model']} (Samples: {demand_meta['training_samples']}, MAE: {demand_meta['selected_metrics']['mae']})")
    print("=" * 60)
    print("All ML models regenerated successfully!")


if __name__ == "__main__":
    main()
