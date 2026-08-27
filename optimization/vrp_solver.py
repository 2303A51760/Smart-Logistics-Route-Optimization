import math
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from optimization.distance_matrix import (
    compute_distance_matrix_meters,
    compute_time_matrix_seconds,
    haversine_distance_km,
)

logger = logging.getLogger(__name__)

# Try importing Google OR-Tools
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logger.warning("OR-Tools not available in python path, fallback heuristic solver will be used.")


class VRPSolver:
    """Enterprise-grade Vehicle Routing Problem solver supporting:
    - Capacitated Vehicle Routing Problem (CVRP)
    - Vehicle Routing Problem with Time Windows (VRPTW)
    - Heterogeneous vehicle fleet capacities
    - Maximum distance/time constraints
    - Priority-weighted disjunctions (URGENT, HIGH, NORMAL, LOW)
    """

    def __init__(self):
        self.is_ortools_ready = ORTOOLS_AVAILABLE

    def solve_vrp(
        self,
        depot: Dict[str, Any],
        orders: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        max_route_distance_km: float = 250.0,
        average_speed_kmh: float = 40.0,
        time_limit_seconds: int = 5,
    ) -> Dict[str, Any]:
        """Solves CVRP / VRPTW with Google OR-Tools.
        
        depot: {"id": str, "name": str, "lat": float, "lng": float}
        orders: list of {"id": str, "name": str, "lat": float, "lng": float, "weight_kg": float, "priority": str, "time_window_start_sec": int, "time_window_end_sec": int}
        vehicles: list of {"id": str, "driver_id": str, "name": str, "capacity_kg": float}
        """
        job_id = f"opt-{uuid.uuid4().hex[:8]}"

        if not orders:
            return {
                "job_id": job_id,
                "status": "COMPLETED",
                "total_distance_km": 0.0,
                "total_duration_min": 0.0,
                "vehicles_used": 0,
                "orders_assigned": 0,
                "orders_unassigned": 0,
                "optimization_score": 100.0,
                "routes": [],
                "unassigned_orders": [],
            }

        if not vehicles:
            vehicles = [{"id": "veh-default", "driver_id": "drv-default", "name": "Default Van", "capacity_kg": 1000.0}]

        # Prepare unified locations list: Index 0 is always the Depot
        locations = [
            {
                "id": depot.get("id", "depot-0"),
                "name": depot.get("name", "Warehouse Depot"),
                "lat": depot["lat"],
                "lng": depot["lng"],
                "demand": 0.0,
                "priority": "NORMAL",
                "time_window": (0, 86400),  # 24 hours in seconds
            }
        ]

        priority_weights = {
            "URGENT": 1000000,
            "HIGH": 500000,
            "NORMAL": 100000,
            "LOW": 20000,
        }

        for ord_item in orders:
            tw_start = ord_item.get("time_window_start_sec", 0)
            tw_end = ord_item.get("time_window_end_sec", 86400)
            if tw_end <= tw_start:
                tw_end = tw_start + 7200  # 2-hour default window

            locations.append({
                "id": ord_item["id"],
                "name": ord_item.get("name", f"Order {ord_item['id']}"),
                "lat": ord_item["lat"],
                "lng": ord_item["lng"],
                "demand": float(ord_item.get("weight_kg", 5.0)),
                "priority": ord_item.get("priority", "NORMAL"),
                "penalty": priority_weights.get(ord_item.get("priority", "NORMAL"), 100000),
                "time_window": (tw_start, tw_end),
            })

        coords = [(loc["lat"], loc["lng"]) for loc in locations]
        dist_matrix = compute_distance_matrix_meters(coords)
        time_matrix = compute_time_matrix_seconds(coords, speed_kmh=average_speed_kmh, service_time_seconds=300)

        if self.is_ortools_ready:
            try:
                return self._solve_with_ortools(
                    job_id=job_id,
                    depot=depot,
                    locations=locations,
                    vehicles=vehicles,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    max_distance_meters=int(max_route_distance_km * 1000),
                    time_limit_seconds=time_limit_seconds,
                )
            except Exception as e:
                logger.error(f"OR-Tools solver failed with error: {e}. Falling back to heuristic solver.", exc_info=True)

        return self._solve_with_heuristic(
            job_id=job_id,
            depot=depot,
            locations=locations,
            vehicles=vehicles,
            dist_matrix=dist_matrix,
        )

    def _solve_with_ortools(
        self,
        job_id: str,
        depot: Dict[str, Any],
        locations: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        dist_matrix: List[List[int]],
        time_matrix: List[List[int]],
        max_distance_meters: int,
        time_limit_seconds: int,
    ) -> Dict[str, Any]:
        num_vehicles = len(vehicles)
        num_locations = len(locations)

        # Manager & Model
        manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        # 1. Distance & Transit Callback
        def distance_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # 2. Vehicle Capacity Dimension (CVRP)
        demands = [int(loc["demand"]) for loc in locations]

        def demand_callback(from_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        vehicle_capacities = [int(v.get("capacity_kg", 500.0)) for v in vehicles]

        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            vehicle_capacities,  # vehicle maximum capacities
            True,  # start cumul to zero
            "Capacity",
        )

        # 3. Time Windows Dimension (VRPTW)
        def time_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_matrix[from_node][to_node]

        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            3600,  # allow 1 hour waiting time slack
            86400,  # maximum time per vehicle (24h)
            False,  # don't force start cumul to zero
            "Time",
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        # Add time window constraints for each order node (skip depot index 0)
        for node_idx in range(1, num_locations):
            index = manager.NodeToIndex(node_idx)
            tw = locations[node_idx]["time_window"]
            time_dimension.CumulVar(index).SetRange(tw[0], tw[1])

        # 4. Max Distance Dimension Constraint
        routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            max_distance_meters,  # max distance per vehicle
            True,  # start cumul to zero
            "Distance",
        )

        # 5. Allow dropping nodes with priority penalties (Disjunctions)
        for node_idx in range(1, num_locations):
            index = manager.NodeToIndex(node_idx)
            penalty = locations[node_idx].get("penalty", 100000)
            routing.AddDisjunction([index], penalty)

        # Search Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = time_limit_seconds

        # Solve
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            logger.warning("OR-Tools found no feasible solution within constraints; using heuristic fallback.")
            return self._solve_with_heuristic(job_id, depot, locations, vehicles, dist_matrix)

        routes = []
        assigned_node_indices = set()
        total_dist_meters = 0
        total_duration_sec = 0

        for v_idx, vehicle in enumerate(vehicles):
            index = routing.Start(v_idx)
            stops = []
            route_dist = 0
            route_load = 0

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                loc = locations[node_index]
                if node_index != 0:
                    assigned_node_indices.add(node_index)

                time_var = time_dimension.CumulVar(index)
                est_arrival_sec = solution.Min(time_var)
                est_arrival_min = round(est_arrival_sec / 60.0, 1)

                stops.append({
                    "sequence": len(stops),
                    "stop_type": "DEPOT" if node_index == 0 else "DELIVERY",
                    "order_id": None if node_index == 0 else loc["id"],
                    "name": loc["name"],
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                    "demand_kg": loc["demand"],
                    "priority": loc.get("priority", "NORMAL"),
                    "estimated_arrival_minutes": est_arrival_min,
                })

                previous_index = index
                index = solution.Value(routing.NextVar(index))
                arc_dist = routing.GetArcCostForVehicle(previous_index, index, v_idx)
                route_dist += arc_dist
                route_load += loc["demand"]

            # Return to depot final stop
            node_index = manager.IndexToNode(index)
            loc = locations[node_index]
            time_var = time_dimension.CumulVar(index)
            est_return_min = round(solution.Min(time_var) / 60.0, 1)

            stops.append({
                "sequence": len(stops),
                "stop_type": "DEPOT",
                "order_id": None,
                "name": f"{loc['name']} (Return)",
                "latitude": loc["lat"],
                "longitude": loc["lng"],
                "demand_kg": 0.0,
                "priority": "NORMAL",
                "estimated_arrival_minutes": est_return_min,
            })

            # Only record non-empty routes (more than just start + return depot)
            if len(stops) > 2:
                dist_km = round(route_dist / 1000.0, 2)
                dur_min = round(est_return_min, 1)
                total_dist_meters += route_dist
                total_duration_sec += int(est_return_min * 60)

                routes.append({
                    "vehicle_id": vehicle["id"],
                    "vehicle_name": vehicle.get("name", f"Vehicle {vehicle['id']}"),
                    "driver_id": vehicle.get("driver_id"),
                    "total_distance_km": dist_km,
                    "estimated_duration_min": dur_min,
                    "capacity_kg": vehicle.get("capacity_kg", 500.0),
                    "total_load_kg": round(route_load, 1),
                    "stops_count": len(stops) - 2,  # excluding start/end depots
                    "stops": stops,
                })

        # Calculate unassigned orders
        unassigned_orders = []
        for node_idx in range(1, num_locations):
            if node_idx not in assigned_node_indices:
                loc = locations[node_idx]
                unassigned_orders.append({
                    "order_id": loc["id"],
                    "name": loc["name"],
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                    "demand_kg": loc["demand"],
                    "priority": loc["priority"],
                    "reason": "Exceeded vehicle capacity or delivery time window limits",
                })

        total_km = round(total_dist_meters / 1000.0, 2)
        total_min = round(total_duration_sec / 60.0, 1)
        total_orders_count = num_locations - 1
        orders_assigned_count = len(assigned_node_indices)

        # Optimization Score (0 - 100%)
        # Based on proportion of orders served + priority weighting
        if total_orders_count > 0:
            score = round((orders_assigned_count / total_orders_count) * 100.0, 1)
        else:
            score = 100.0

        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "solver": "OR_TOOLS_CVRP_VRPTW",
            "total_distance_km": total_km,
            "total_duration_min": total_min,
            "vehicles_used": len(routes),
            "orders_assigned": orders_assigned_count,
            "orders_unassigned": len(unassigned_orders),
            "optimization_score": score,
            "routes": routes,
            "unassigned_orders": unassigned_orders,
        }

    def _solve_with_heuristic(
        self,
        job_id: str,
        depot: Dict[str, Any],
        locations: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        dist_matrix: List[List[int]],
    ) -> Dict[str, Any]:
        """Greedy nearest neighbor heuristic respecting capacity limits."""
        depot_loc = locations[0]
        delivery_nodes = locations[1:]
        
        routes = []
        unassigned = []
        assigned_count = 0
        total_dist_m = 0
        
        remaining_deliveries = list(delivery_nodes)
        
        for vehicle in vehicles:
            if not remaining_deliveries:
                break
                
            capacity = float(vehicle.get("capacity_kg", 500.0))
            current_load = 0.0
            current_lat, current_lng = depot_loc["lat"], depot_loc["lng"]
            
            stops = [{
                "sequence": 0,
                "stop_type": "DEPOT",
                "order_id": None,
                "name": depot_loc["name"],
                "latitude": depot_loc["lat"],
                "longitude": depot_loc["lng"],
                "demand_kg": 0.0,
                "priority": "NORMAL",
                "estimated_arrival_minutes": 0.0,
            }]
            
            route_dist_km = 0.0
            current_time_min = 0.0
            
            while remaining_deliveries:
                # Find nearest delivery that fits in remaining capacity
                best_idx = -1
                best_dist = float("inf")
                
                for idx, item in enumerate(remaining_deliveries):
                    if current_load + item["demand"] <= capacity:
                        d = haversine_distance_km(current_lat, current_lng, item["lat"], item["lng"])
                        if d < best_dist:
                            best_dist = d
                            best_idx = idx
                            
                if best_idx == -1:
                    # Vehicle is full
                    break
                    
                selected = remaining_deliveries.pop(best_idx)
                current_load += selected["demand"]
                route_dist_km += best_dist
                current_time_min += (best_dist / 40.0) * 60.0 + 5.0  # travel + 5m service
                current_lat, current_lng = selected["lat"], selected["lng"]
                
                stops.append({
                    "sequence": len(stops),
                    "stop_type": "DELIVERY",
                    "order_id": selected["id"],
                    "name": selected["name"],
                    "latitude": selected["lat"],
                    "longitude": selected["lng"],
                    "demand_kg": selected["demand"],
                    "priority": selected.get("priority", "NORMAL"),
                    "estimated_arrival_minutes": round(current_time_min, 1),
                })
                assigned_count += 1
                
            # Return to depot
            return_dist = haversine_distance_km(current_lat, current_lng, depot_loc["lat"], depot_loc["lng"])
            route_dist_km += return_dist
            current_time_min += (return_dist / 40.0) * 60.0
            
            stops.append({
                "sequence": len(stops),
                "stop_type": "DEPOT",
                "order_id": None,
                "name": f"{depot_loc['name']} (Return)",
                "latitude": depot_loc["lat"],
                "longitude": depot_loc["lng"],
                "demand_kg": 0.0,
                "priority": "NORMAL",
                "estimated_arrival_minutes": round(current_time_min, 1),
            })
            
            if len(stops) > 2:
                total_dist_m += int(route_dist_km * 1000)
                routes.append({
                    "vehicle_id": vehicle["id"],
                    "vehicle_name": vehicle.get("name", f"Vehicle {vehicle['id']}"),
                    "driver_id": vehicle.get("driver_id"),
                    "total_distance_km": round(route_dist_km, 2),
                    "estimated_duration_min": round(current_time_min, 1),
                    "capacity_kg": capacity,
                    "total_load_kg": round(current_load, 1),
                    "stops_count": len(stops) - 2,
                    "stops": stops,
                })

        for leftover in remaining_deliveries:
            unassigned.append({
                "order_id": leftover["id"],
                "name": leftover["name"],
                "latitude": leftover["lat"],
                "longitude": leftover["lng"],
                "demand_kg": leftover["demand"],
                "priority": leftover.get("priority", "NORMAL"),
                "reason": "Vehicle capacity exhausted",
            })

        total_orders = len(delivery_nodes)
        score = round((assigned_count / total_orders) * 100.0, 1) if total_orders > 0 else 100.0

        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "solver": "HEURISTIC_NEAREST_NEIGHBOR",
            "total_distance_km": round(total_dist_m / 1000.0, 2),
            "total_duration_min": round(sum(r["estimated_duration_min"] for r in routes), 1),
            "vehicles_used": len(routes),
            "orders_assigned": assigned_count,
            "orders_unassigned": len(unassigned),
            "optimization_score": score,
            "routes": routes,
            "unassigned_orders": unassigned,
        }
