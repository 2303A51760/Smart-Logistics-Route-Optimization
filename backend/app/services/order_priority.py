from typing import Dict, Any, Optional
from app.ml.dataset import haversine_distance


class OrderPriorityEngine:
    """
    Centralized scoring engine for intelligent order prioritization.
    Computes a deterministic, explainable numerical score (0-100) and priority tier.
    """

    MODEL_NAME = "order_priority_heuristic_v1"
    MODEL_VERSION = "1.0.0"

    def calculate_priority_score(
        self,
        order: Dict[str, Any],
        depot_lat: Optional[float] = 40.7128,
        depot_lng: Optional[float] = -74.0060,
    ) -> Dict[str, Any]:
        """
        Calculates priority score from order metadata and operational constraints.
        """
        raw_priority = str(order.get("priority", "NORMAL")).upper()
        weight_kg = float(order.get("package_weight") or order.get("weight") or 5.0)
        status = str(order.get("status", "PENDING")).upper()

        # 1. Base Priority Factor (Max 40 pts)
        priority_weights = {
            "CRITICAL": 40.0,
            "URGENT": 35.0,
            "HIGH": 25.0,
            "MEDIUM": 15.0,
            "NORMAL": 8.0,
            "LOW": 3.0,
        }
        base_score = priority_weights.get(raw_priority, 10.0)

        # 2. Delivery Time Window / Deadline Factor (Max 30 pts)
        window_end = order.get("time_window_end_sec")
        deadline_score = 10.0
        deadline_reason = "Standard delivery window"

        if window_end is not None:
            # If window is small (< 4 hours in sec = 14400), it's highly urgent
            if window_end <= 14400:
                deadline_score = 30.0
                deadline_reason = "Immediate delivery deadline (< 4 hours)"
            elif window_end <= 28800:
                deadline_score = 22.0
                deadline_reason = "Tight delivery window (< 8 hours)"
            elif window_end <= 43200:
                deadline_score = 15.0
                deadline_reason = "Standard 12-hour window"
            else:
                deadline_score = 5.0
                deadline_reason = "Flexible delivery window"

        # 3. Distance from Depot Factor (Max 15 pts)
        dest_lat = float(order.get("delivery_latitude") or order.get("lat") or 0.0)
        dest_lng = float(order.get("delivery_longitude") or order.get("lng") or 0.0)

        distance_km = 0.0
        distance_score = 5.0
        if dest_lat != 0.0 and dest_lng != 0.0 and depot_lat and depot_lng:
            distance_km = haversine_distance(depot_lat, depot_lng, dest_lat, dest_lng)
            if distance_km > 50.0:
                distance_score = 15.0
            elif distance_km > 25.0:
                distance_score = 10.0
            else:
                distance_score = 5.0

        # 4. Package Weight / Handling Load Factor (Max 10 pts)
        weight_score = min(10.0, round((weight_kg / 50.0) * 10.0, 1))

        # 5. Order Status & Backlog Aging Factor (Max 5 pts)
        status_score = 5.0 if status in ["PENDING", "ASSIGNED"] else 2.0

        # Composite Score (0 - 100)
        total_score = min(100.0, round(base_score + deadline_score + distance_score + weight_score + status_score, 1))

        # Classification Tiers
        if total_score >= 85.0:
            priority_tier = "CRITICAL"
            recommendation = "Assign immediately to highest-capacity available driver."
        elif total_score >= 70.0:
            priority_tier = "HIGH"
            recommendation = "Schedule in next dispatch batch with priority routing."
        elif total_score >= 40.0:
            priority_tier = "MEDIUM"
            recommendation = "Include in standard daily vehicle routing optimization."
        else:
            priority_tier = "LOW"
            recommendation = "Consolidate with standard low-density delivery manifests."

        factors = {
            "base_priority_score": round(base_score, 1),
            "deadline_urgency_score": round(deadline_score, 1),
            "distance_score": round(distance_score, 1),
            "distance_km": round(distance_km, 2),
            "weight_load_score": round(weight_score, 1),
            "status_backlog_score": round(status_score, 1),
            "deadline_factor_note": deadline_reason,
        }

        reasons = [
            f"Base order priority rated as {raw_priority} ({base_score:.0f} pts)",
            f"Delivery deadline urgency: {deadline_reason} ({deadline_score:.0f} pts)",
            f"Transit distance from depot: {distance_km:.1f} km ({distance_score:.0f} pts)",
            f"Package weight: {weight_kg:.1f} kg ({weight_score:.0f} pts)",
        ]

        return {
            "order_id": str(order.get("id")),
            "order_number": order.get("order_number") or f"ORD-{str(order.get('id'))[:8]}",
            "score": total_score,
            "priority": priority_tier,
            "raw_priority": raw_priority,
            "factors": factors,
            "reasons": reasons,
            "recommendation": recommendation,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
        }


order_priority_engine = OrderPriorityEngine()
