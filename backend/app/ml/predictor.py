import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import joblib
import pandas as pd

from app.ml.features import extract_feature_dict
from app.ml.trainer import MODEL_PATH, METADATA_PATH, MODEL_VERSION, train_eta_model

logger = logging.getLogger(__name__)


class ETAPredictionService:
    """
    Production ETA Prediction Service with ML inference and deterministic fallback.
    """

    def __init__(self):
        self._pipeline = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._load_model_artifacts()

    def _load_model_artifacts(self):
        """Loads trained pipeline and metadata if available, or trains baseline if missing."""
        try:
            if MODEL_PATH.exists() and METADATA_PATH.exists():
                self._pipeline = joblib.load(MODEL_PATH)
                with open(METADATA_PATH, "r") as f:
                    self._metadata = json.load(f)
                logger.info(f"Loaded ETA model: {self._metadata.get('selected_model')} ({self._metadata.get('model_version')})")
            else:
                # Auto-initialize baseline model artifact
                logger.info("Initializing baseline ETA model artifact...")
                self._metadata = train_eta_model()
                self._pipeline = joblib.load(MODEL_PATH)
        except Exception as e:
            logger.warning(f"Could not load ML ETA model artifacts ({e}). Fallback mode active.")
            self._pipeline = None
            self._metadata = None

    def reload(self):
        """Reloads artifacts after on-demand retraining."""
        self._load_model_artifacts()

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model performance and training metadata."""
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
            "selected_model": "Deterministic Analytical Fallback",
            "trained_at": None,
            "training_samples": 0,
            "status": "FALLBACK_ACTIVE",
            "selected_metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
        }

    def predict_eta(
        self,
        input_data: Dict[str, Any],
        base_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Predicts delivery journey duration in minutes and estimated arrival time.
        Uses Scikit-Learn model if available; otherwise falls back gracefully to deterministic calculation.
        """
        ref_time = base_time or datetime.utcnow()
        dist_km = max(0.1, float(input_data.get("distance_km", 5.0)))
        stop_seq = max(1, int(input_data.get("stop_sequence", 1)))

        # 1. Attempt Machine Learning Prediction
        if self._pipeline is not None:
            try:
                feat_dict = extract_feature_dict(input_data)
                df_single = pd.DataFrame([feat_dict])
                predicted_dur = float(self._pipeline.predict(df_single)[0])
                predicted_dur = round(max(3.0, predicted_dur), 1)

                mae_err = 3.5
                if self._metadata and "selected_metrics" in self._metadata:
                    mae_err = self._metadata["selected_metrics"].get("mae", 3.5)

                eta_dt = ref_time + timedelta(minutes=predicted_dur)

                return {
                    "predicted_duration_minutes": predicted_dur,
                    "estimated_arrival": eta_dt.isoformat(),
                    "source": "ML",
                    "model_version": self._metadata.get("model_version", MODEL_VERSION) if self._metadata else MODEL_VERSION,
                    "confidence_interval_min": round(max(1.0, predicted_dur - mae_err), 1),
                    "confidence_interval_max": round(predicted_dur + mae_err, 1),
                }
            except Exception as e:
                logger.warning(f"ML ETA prediction failed: {e}. Falling back to deterministic estimation.")

        # 2. Deterministic Analytical Fallback (~28 km/h urban average speed + 4.5 min per stop)
        avg_speed_kmh = 28.0
        base_travel_minutes = (dist_km / avg_speed_kmh) * 60.0
        stop_handling_minutes = stop_seq * 4.5
        fallback_dur = round(max(5.0, base_travel_minutes + stop_handling_minutes), 1)
        fallback_eta = ref_time + timedelta(minutes=fallback_dur)

        return {
            "predicted_duration_minutes": fallback_dur,
            "estimated_arrival": fallback_eta.isoformat(),
            "source": "FALLBACK",
            "model_version": "deterministic-v1",
            "confidence_interval_min": round(max(1.0, fallback_dur * 0.85), 1),
            "confidence_interval_max": round(fallback_dur * 1.25, 1),
            "reason": "MODEL_UNAVAILABLE_OR_FALLBACK_REQUESTED",
        }


eta_service = ETAPredictionService()
