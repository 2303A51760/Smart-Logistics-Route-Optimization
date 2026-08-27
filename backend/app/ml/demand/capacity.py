import math
from typing import Dict, Any, Optional, List
from app.core.logistics_store import SEED_DRIVERS, SEED_VEHICLES, SEED_WAREHOUSES

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

        # Gather asset counts
        drivers_count = (
            active_drivers
            if active_drivers is not None
            else max(2, len([d for d in SEED_DRIVERS.values() if d.get("status") in ["AVAILABLE", "ASSIGNED"]]))
        )
        vehicles_count = (
            active_vehicles
            if active_vehicles is not None
            else max(2, len([v for v in SEED_VEHICLES.values() if v.get("status") in ["AVAILABLE", "IN_TRANSIT"]]))
        )

        wh_id = forecast_result.get("warehouse_id")
        wh_cap = warehouse_capacity
        if wh_cap is None:
            if wh_id and wh_id in SEED_WAREHOUSES:
                wh_cap = float(SEED_WAREHOUSES[wh_id].get("capacity", 20000.0))
            else:
                wh_cap = sum(float(w.get("capacity", 20000.0)) for w in SEED_WAREHOUSES.values())

        # Fleet Capacity calculations
        effective_active_fleet = min(drivers_count, vehicles_count)
        daily_fleet_capacity = effective_active_fleet * AVERAGE_ORDERS_PER_DRIVER_PER_DAY
        total_period_capacity = int(round(daily_fleet_capacity * horizon_days))

        # Utilization & Gap
        if total_period_capacity > 0:
            utilization_pct = round((total_forecasted_demand / total_period_capacity) * 100.0, 1)
        else:
            utilization_pct = 100.0

        capacity_gap = int(total_forecasted_demand - total_period_capacity)

        # Requirements
        required_drivers = max(1, math.ceil(daily_average_demand / AVERAGE_ORDERS_PER_DRIVER_PER_DAY))
        required_vehicles = required_drivers

        # Status Category
        if utilization_pct > 100.0:
            status = "OVER_CAPACITY"
        elif utilization_pct >= 85.0:
            status = "HIGH_UTILIZATION"
        elif utilization_pct >= 60.0:
            status = "NORMAL"
        else:
            status = "UNDER_UTILIZED"

        return {
            "horizon_days": horizon_days,
            "forecasted_total_demand": total_forecasted_demand,
            "daily_average_demand": round(daily_average_demand, 1),
            "peak_daily_demand": max([int(item.get("predicted_orders", 0)) for item in forecast_items], default=0),
            "available_capacity": total_period_capacity,
            "capacity_utilization_percent": utilization_pct,
            "capacity_gap": capacity_gap,
            "status": status,
            "active_drivers": drivers_count,
            "active_vehicles": vehicles_count,
            "required_drivers": required_drivers,
            "required_vehicles": required_vehicles,
            "warehouse_capacity_kg": wh_cap,
            "assumptions": {
                "average_orders_per_driver_per_day": AVERAGE_ORDERS_PER_DRIVER_PER_DAY,
                "average_package_weight_kg": AVERAGE_PACKAGE_WEIGHT_KG,
            },
        }


capacity_service = CapacityPlanningService()
