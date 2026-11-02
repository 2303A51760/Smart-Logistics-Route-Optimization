from typing import Dict, Any, Optional
from app.core.config import settings


class CostAndFuelEstimator:
    """
    Computes transparent fuel consumption and route operational cost estimates.
    """

    MODEL_NAME = "cost_fuel_estimator_v1"
    MODEL_VERSION = "1.0.0"

    def estimate_route_cost(
        self,
        distance_km: float,
        duration_minutes: float,
        vehicle_type: Optional[str] = "VAN",
        load_kg: float = 50.0,
        vehicle_capacity_kg: float = 500.0,
        fuel_cost_per_liter: Optional[float] = None,
        driver_hourly_rate: float = 22.50,
    ) -> Dict[str, Any]:
        """
        Calculates fuel burn and operational costs with vehicle class adjustments.
        """
        cost_per_liter = fuel_cost_per_liter or settings.FUEL_COST_PER_LITER
        base_consumption_per_100km = settings.AVG_FUEL_CONSUMPTION_L_PER_100KM

        # Vehicle type efficiency adjustment
        veh_type_upper = str(vehicle_type or "VAN").upper()
        if "TRUCK" in veh_type_upper or "HEAVY" in veh_type_upper:
            base_consumption_per_100km = 22.0
        elif "VAN" in veh_type_upper:
            base_consumption_per_100km = 12.5
        elif "BIKE" in veh_type_upper or "SCOOTER" in veh_type_upper:
            base_consumption_per_100km = 4.0

        # Load factor penalty (0% to +20% additional fuel under full cargo load)
        load_ratio = min(1.0, max(0.0, load_kg / max(1.0, vehicle_capacity_kg)))
        adjusted_consumption_per_100km = base_consumption_per_100km * (1.0 + (0.20 * load_ratio))

        # Fuel in liters
        estimated_fuel_liters = round((distance_km / 100.0) * adjusted_consumption_per_100km, 2)
        estimated_fuel_cost = round(estimated_fuel_liters * cost_per_liter, 2)

        # Labor cost
        estimated_labor_cost = round((duration_minutes / 60.0) * driver_hourly_rate, 2)

        # Total operational cost
        total_estimated_cost = round(estimated_fuel_cost + estimated_labor_cost, 2)

        return {
            "distance_km": round(distance_km, 2),
            "estimated_duration_minutes": round(duration_minutes, 1),
            "estimated_fuel_liters": estimated_fuel_liters,
            "fuel_cost_per_liter": cost_per_liter,
            "estimated_fuel_cost": estimated_fuel_cost,
            "estimated_labor_cost": estimated_labor_cost,
            "estimated_total_cost": total_estimated_cost,
            "currency": "USD",
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
        }


cost_fuel_estimator = CostAndFuelEstimator()
