from typing import List, Dict, Any, Optional
from optimization.vrp_solver import VRPSolver


class RouteOptimizer:
    """Coordinates high-level business constraints (Warehouses, Orders, Fleet Vehicles,
    Drivers, Working Hours) and executes the VRPSolver to generate executable route plans.
    """

    def __init__(self):
        self.solver = VRPSolver()

    def optimize_dispatch(
        self,
        warehouse: Dict[str, Any],
        orders: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        drivers: Optional[List[Dict[str, Any]]] = None,
        max_route_distance_km: float = 250.0,
        average_speed_kmh: float = 40.0,
        time_limit_seconds: int = 5,
    ) -> Dict[str, Any]:
        """Maps database objects into solver inputs and pairs drivers to vehicles."""
        # Pair drivers with vehicles if drivers list is provided
        driver_map = {d["id"]: d for d in (drivers or [])}

        prepared_vehicles = []
        for i, veh in enumerate(vehicles):
            driver_id = veh.get("assigned_driver_id")
            if not driver_id and drivers and i < len(drivers):
                driver_id = drivers[i]["id"]

            driver_info = driver_map.get(driver_id, {})
            driver_name = driver_info.get("name") or driver_info.get("user_name")

            prepared_vehicles.append({
                "id": veh["id"],
                "name": veh.get("plate_number") or veh.get("model") or f"Vehicle {veh['id']}",
                "driver_id": driver_id,
                "driver_name": driver_name,
                "capacity_kg": float(veh.get("capacity_kg") or veh.get("capacity") or 500.0),
            })

        prepared_orders = []
        for ord_item in orders:
            prepared_orders.append({
                "id": ord_item["id"],
                "name": ord_item.get("order_number") or f"Order #{ord_item['id'][:8]}",
                "customer_name": ord_item.get("customer_name") or "Customer",
                "lat": float(ord_item.get("delivery_latitude") or ord_item.get("lat") or 0.0),
                "lng": float(ord_item.get("delivery_longitude") or ord_item.get("lng") or 0.0),
                "weight_kg": float(ord_item.get("package_weight") or ord_item.get("weight") or 5.0),
                "priority": ord_item.get("priority", "NORMAL"),
                "time_window_start_sec": ord_item.get("time_window_start_sec", 0),
                "time_window_end_sec": ord_item.get("time_window_end_sec", 86400),
            })

        depot = {
            "id": warehouse.get("id", "warehouse-main"),
            "name": warehouse.get("name", "Warehouse Depot"),
            "lat": float(warehouse.get("latitude") or warehouse.get("lat") or 40.7128),
            "lng": float(warehouse.get("longitude") or warehouse.get("lng") or -74.0060),
        }

        result = self.solver.solve_vrp(
            depot=depot,
            orders=prepared_orders,
            vehicles=prepared_vehicles,
            max_route_distance_km=max_route_distance_km,
            average_speed_kmh=average_speed_kmh,
            time_limit_seconds=time_limit_seconds,
        )

        # Attach driver names back to the generated routes for clarity
        for route in result.get("routes", []):
            drv_id = route.get("driver_id")
            if drv_id and drv_id in driver_map:
                route["driver_name"] = driver_map[drv_id].get("name") or driver_map[drv_id].get("user_name")

        return result
