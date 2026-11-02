import math
from typing import Dict, Any, Optional

# Documented Operational Assumptions
AVERAGE_ORDERS_PER_DRIVER_PER_DAY = 25.0
AVERAGE_PACKAGE_WEIGHT_KG = 8.5


class CapacityPlanningService:
    """
    Computes logistics capacity utilization, workload gaps, and driver/vehicle
    allocation requirements grounded in active fleet assets.
    """

    @staticmethod
    def calculate_capacity_plan(
        forecast_result: Dict[str, Any],
        active_drivers: Optional[int] = None,
        active_vehicles: Optional[int] = None,
        warehouse_capacity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates fleet and facility capacity against forecasted demand volume.
        """
        forecast_items = forecast_result.get("forecast", [])
        horizon_days = max(1, int(forecast_result.get("horizon_days", len(forecast_items) or 7)))
        total_forecasted_demand = sum(int(item.get("predicted_orders", 0)) for item in forecast_items)
        daily_average_demand = total_forecasted_demand / horizon_days if horizon_days > 0 else 0.0
        peak_daily_demand = max([int(item.get("predicted_orders", 0)) for item in forecast_items], default=0)

        # Gather asset counts
        drivers_count = active_drivers if active_drivers is not None else 2
        vehicles_count = active_vehicles if active_vehicles is not None else 2
        wh_cap = warehouse_capacity if warehouse_capacity is not None else 25000.0

        # Fleet Capacity calculations
        effective_active_fleet = min(drivers_count, vehicles_count)
        daily_fleet_capacity = effective_active_fleet * AVERAGE_ORDERS_PER_DRIVER_PER_DAY
        total_period_capacity = int(round(daily_fleet_capacity * horizon_days))

        # Utilization & Gap
        if total_period_capacity > 0:
            utilization_pct = round((total_forecasted_demand / total_period_capacity) * 100.0, 1)
        else:
            utilization_pct = 100.0

        capacity_gap = total_forecasted_demand - total_period_capacity
        required_drivers = int(math.ceil(total_forecasted_demand / (AVERAGE_ORDERS_PER_DRIVER_PER_DAY * horizon_days))) if horizon_days > 0 else 0
        required_vehicles = required_drivers

        # Status categorization
        if utilization_pct > 105.0:
            status = "OVER_CAPACITY"
        elif utilization_pct >= 90.0:
            status = "HIGH_UTILIZATION"
        elif utilization_pct < 60.0:
            status = "UNDER_UTILIZED"
        else:
            status = "NORMAL"

        return {
            "horizon_days": horizon_days,
            "forecasted_total_demand": total_forecasted_demand,
            "daily_average_demand": round(daily_average_demand, 1),
            "peak_daily_demand": peak_daily_demand,
            "available_capacity": total_period_capacity,
            "capacity_utilization_percent": utilization_pct,
            "capacity_gap": capacity_gap,
            "demand_gap": capacity_gap,
            "status": status,
            "active_drivers": drivers_count,
            "active_drivers_count": drivers_count,
            "active_vehicles": vehicles_count,
            "active_vehicles_count": vehicles_count,
            "required_drivers": required_drivers,
            "required_vehicles": required_vehicles,
            "warehouse_capacity_kg": wh_cap,
            "assumptions": {
                "average_orders_per_driver_per_day": AVERAGE_ORDERS_PER_DRIVER_PER_DAY,
                "average_package_weight_kg": AVERAGE_PACKAGE_WEIGHT_KG,
            },
        }


capacity_service = CapacityPlanningService()
