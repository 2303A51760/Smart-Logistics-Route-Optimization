import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn not available, using analytical ETA model.")


class ETAPredictor:
    """Predicts realistic estimated time of arrival (ETA) incorporating traffic & weather factors."""

    def __init__(self):
        self.is_trained = False
        self.model = None
        if SKLEARN_AVAILABLE:
            self.model = GradientBoostingRegressor(n_estimators=50, random_state=42)

    def train_baseline(self):
        """Train baseline model with synthetic routing parameters."""
        if not SKLEARN_AVAILABLE:
            return
        # Features: [distance_km, stops_count, hour_of_day, weather_factor (1=Clear, 2=Rain, 3=Snow), traffic_index (1.0 - 2.5)]
        X = np.array([
            [5.0, 2, 9, 1, 1.2],
            [12.0, 4, 14, 1, 1.0],
            [25.0, 8, 17, 2, 2.0],
            [3.0, 1, 8, 1, 1.5],
            [18.0, 5, 12, 1, 1.1],
            [30.0, 10, 18, 3, 2.3],
            [8.0, 3, 21, 1, 0.9],
        ])
        # Target: Duration in minutes
        y = np.array([15.0, 28.0, 68.0, 11.0, 39.0, 85.0, 17.0])
        self.model.fit(X, y)
        self.is_trained = True

    def predict_eta_minutes(
        self,
        distance_km: float,
        stops_count: int = 1,
        hour_of_day: int = 12,
        weather_factor: int = 1,
        traffic_index: float = 1.2,
    ) -> float:
        """Predict journey ETA in minutes."""
        if SKLEARN_AVAILABLE:
            if not self.is_trained:
                self.train_baseline()
            X_new = np.array([[distance_km, stops_count, hour_of_day, weather_factor, traffic_index]])
            pred = self.model.predict(X_new)[0]
            return max(1.0, round(float(pred), 1))

        # Fallback analytical calculation: ~30km/h avg + 4 min per stop + traffic multiplier
        base_travel_time = (distance_km / 30.0) * 60.0 * traffic_index
        stop_time = stops_count * 4.0
        weather_multiplier = 1.0 + (weather_factor - 1) * 0.15
        total_time = (base_travel_time + stop_time) * weather_multiplier
        return round(max(1.0, total_time), 1)
