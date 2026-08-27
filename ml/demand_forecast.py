import math
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DemandForecaster:
    """Predicts delivery demand per zone and time-of-day for fleet sizing."""

    def __init__(self):
        pass

    def forecast_zone_demand(self, zone_id: str, day_of_week: int, hour: int) -> Dict[str, Any]:
        """Calculates expected package volume and recommended fleet count."""
        # Simple seasonal sinusoidal demand index
        base_demand = 45.0
        peak_multiplier = 1.0 + 0.6 * math.sin((hour - 8) * math.pi / 8) if 8 <= hour <= 20 else 0.3
        weekday_factor = 1.2 if day_of_week in [1, 2, 3, 4, 5] else 0.7

        estimated_packages = int(base_demand * max(0.1, peak_multiplier) * weekday_factor)
        recommended_vehicles = max(1, math.ceil(estimated_packages / 20))

        return {
            "zone_id": zone_id,
            "day_of_week": day_of_week,
            "hour": hour,
            "estimated_packages": estimated_packages,
            "recommended_vehicles": recommended_vehicles,
            "congestion_risk": "HIGH" if peak_multiplier > 1.3 else ("MEDIUM" if peak_multiplier > 0.8 else "LOW"),
        }
