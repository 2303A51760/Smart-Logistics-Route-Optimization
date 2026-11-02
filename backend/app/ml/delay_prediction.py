import logging
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class DeliveryDelayPredictor:
    """
    ML/Statistical model for predicting delivery delay risk and probability.
    Provides explainable factor attribution for logistics dispatchers.
    """

    MODEL_NAME = "gradient_boosting_delay_risk" if SKLEARN_AVAILABLE else "baseline_statistical_delay_risk"
    MODEL_VERSION = "1.0.0"

    def __init__(self):
        self.is_trained = False
        self.classifier = None
        if SKLEARN_AVAILABLE:
            self.classifier = GradientBoostingClassifier(n_estimators=40, random_state=42)

    def _train_baseline(self):
        if not SKLEARN_AVAILABLE:
            return
        # Features: [distance_km, stops_count, hour_of_day, weather_factor (1=Clear, 2=Rain, 3=Snow), traffic_index (1.0-2.5), weight_kg]
        X = np.array([
            [5.0, 2, 9, 1, 1.1, 5.0],
            [15.0, 4, 17, 2, 1.9, 12.0],
            [35.0, 8, 18, 3, 2.2, 45.0],
            [8.0, 3, 11, 1, 1.2, 8.0],
            [22.0, 6, 17, 2, 2.0, 30.0],
            [3.0, 1, 10, 1, 1.0, 3.0],
            [40.0, 9, 19, 3, 2.4, 60.0],
            [12.0, 3, 14, 1, 1.3, 15.0],
        ])
        # Target: 0 (No significant delay), 1 (High risk of delay)
        y = np.array([0, 1, 1, 0, 1, 0, 1, 0])
        self.classifier.fit(X, y)
        self.is_trained = True

    def predict_delay_risk(
        self,
        order_id: str,
        distance_km: float,
        stops_count: int = 1,
        hour_of_day: int = 14,
        weather_factor: int = 1,
        traffic_index: float = 1.2,
        weight_kg: float = 10.0,
        deadline_minutes_remaining: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Estimates delay probability (0.0 - 1.0), risk tier, and predicted delay duration.
        """
        reasons = []

        # Calculate baseline probability via statistical heuristics + ML inference
        if SKLEARN_AVAILABLE:
            if not self.is_trained:
                self._train_baseline()
            X_new = np.array([[distance_km, stops_count, hour_of_day, weather_factor, traffic_index, weight_kg]])
            probs = self.classifier.predict_proba(X_new)[0]
            ml_delay_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
            confidence = 0.85
        else:
            # Analytical baseline
            base_risk = min(0.4, (distance_km / 100.0) * 0.4)
            traffic_risk = max(0.0, (traffic_index - 1.0) * 0.3)
            weather_risk = (weather_factor - 1) * 0.15
            stops_risk = min(0.2, stops_count * 0.03)
            ml_delay_prob = min(0.95, base_risk + traffic_risk + weather_risk + stops_risk)
            confidence = 0.75

        # Incorporate deadline pressure if known
        if deadline_minutes_remaining is not None:
            est_travel_mins = (distance_km / 35.0) * 60.0 * traffic_index + (stops_count * 5.0)
            if est_travel_mins > deadline_minutes_remaining:
                ml_delay_prob = max(ml_delay_prob, 0.85)
                reasons.append(f"Estimated journey duration ({est_travel_mins:.0f}m) exceeds remaining deadline ({deadline_minutes_remaining:.0f}m)")
            elif est_travel_mins > deadline_minutes_remaining * 0.8:
                ml_delay_prob = max(ml_delay_prob, 0.65)
                reasons.append("Journey ETA is close to customer delivery deadline window")

        # Explainability reasoning
        if traffic_index >= 1.5:
            reasons.append(f"High traffic congestion index ({traffic_index:.1f}x normal latency)")
        if stops_count >= 5:
            reasons.append(f"High stop density on route ({stops_count} intermediate waypoints)")
        if weather_factor >= 2:
            reasons.append("Adverse weather conditions slowing fleet average velocity")
        if distance_km >= 30.0:
            reasons.append(f"Long transit corridor distance ({distance_km:.1f} km)")
        if not reasons:
            reasons.append("Optimal transit conditions and sufficient delivery buffer")

        # Risk Classification
        delay_prob = round(float(ml_delay_prob), 2)
        if delay_prob >= 0.75:
            risk_level = "HIGH"
            predicted_delay_mins = int(25 + (delay_prob * 30))
            recommendation = "Consider route re-optimization or priority vehicle re-assignment."
        elif delay_prob >= 0.45:
            risk_level = "MEDIUM"
            predicted_delay_mins = int(10 + (delay_prob * 15))
            recommendation = "Monitor live driver telemetry and notify customer of potential window shift."
        else:
            risk_level = "LOW"
            predicted_delay_mins = 0
            recommendation = "On schedule for on-time delivery completion."

        return {
            "order_id": order_id,
            "delay_probability": delay_prob,
            "risk_level": risk_level,
            "predicted_delay_minutes": predicted_delay_mins,
            "confidence": confidence,
            "factors": reasons,
            "recommendation": recommendation,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
        }


delay_predictor = DeliveryDelayPredictor()
