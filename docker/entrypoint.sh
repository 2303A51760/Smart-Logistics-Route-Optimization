#!/bin/sh
set -e

echo "=== Smart Logistics Backend Initializing ==="

# 1. Ensure ML model artifacts exist
if [ ! -f "/app/backend/app/ml/artifacts/eta_model.joblib" ] || [ ! -f "/app/backend/app/ml/demand/artifacts/demand_model.joblib" ]; then
    echo "[Entrypoint] ML model artifacts not found. Training baseline models..."
    python scripts/train_models.py || echo "[Entrypoint] Model training completed or fallback active."
else
    echo "[Entrypoint] ML model artifacts verified."
fi

# 2. For development/testing mode: auto-apply migrations and seed data ONLY in development or test
if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "test" ]; then
    echo "[Entrypoint] Development/test environment ($ENVIRONMENT) detected."
    echo "[Entrypoint] Running database migrations (alembic upgrade head)..."
    cd /app/backend
    alembic upgrade head || echo "[Entrypoint] Alembic upgrade completed or table already at head."
    cd /app

    echo "[Entrypoint] Checking and seeding demo data..."
    python scripts/seed_demo_data.py || echo "[Entrypoint] Seeding completed or skipped."
else
    echo "[Entrypoint] Production or non-development environment ($ENVIRONMENT) detected. Skipping automatic dev migrations and seeding."
fi

echo "=== Smart Logistics Backend Starting Service ==="
exec "$@"

