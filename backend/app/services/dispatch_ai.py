from typing import List, Dict, Any, Optional
from app.ml.dataset import haversine_distance


class DispatchAIEngine:
    """
    AI-Assisted Driver and Vehicle Assignment Engine.
    Ranks compatible drivers and vehicles with full explainability.
    """

    MODEL_NAME = "dispatch_matcher_v1"
    MODEL_VERSION = "1.0.0"

    def rank_assignments_for_order(
        self,
        order: Dict[str, Any],
        drivers: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        warehouse: Optional[Dict[str, Any]] = None,
        maintenance_records: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates ranked driver-vehicle pairing recommendations for a target order.
        """
        order_id = str(order.get("id"))
        order_weight = float(order.get("package_weight") or order.get("weight") or 5.0)

        depot_lat = float(warehouse.get("latitude") if warehouse else 40.7128)
        depot_lng = float(warehouse.get("longitude") if warehouse else -74.0060)

        # Build maintenance lookup: set of vehicle_ids currently under maintenance
        vehicles_under_maintenance = set()
        for m in (maintenance_records or []):
            if str(m.get("status", "")).upper() in ["SCHEDULED", "IN_PROGRESS"]:
                vehicles_under_maintenance.add(str(m.get("vehicle_id")))

        # Map vehicles by driver_id or create vehicle pool
        assigned_vehicles = {str(v.get("assigned_driver_id")): v for v in vehicles if v.get("assigned_driver_id")}
        unassigned_vehicles = [v for v in vehicles if not v.get("assigned_driver_id")]

        candidates = []

        for drv in drivers:
            driver_id = str(drv.get("id"))
            driver_name = drv.get("name") or drv.get("user_name") or f"Driver {driver_id[:6]}"
            driver_status = str(drv.get("status", "AVAILABLE")).upper()

            # Find matching or unassigned vehicle
            veh = assigned_vehicles.get(driver_id)
            if not veh and unassigned_vehicles:
                veh = unassigned_vehicles[0]
            if not veh and vehicles:
                veh = vehicles[0]
            if not veh:
                continue

            vehicle_id = str(veh.get("id"))
            vehicle_name = veh.get("plate_number") or veh.get("model") or f"Vehicle {vehicle_id[:6]}"
            vehicle_capacity = float(veh.get("capacity_kg") or veh.get("capacity") or 500.0)
            vehicle_status = str(veh.get("status", "AVAILABLE")).upper()

            reasons = []
            score = 0.0

            # 1. Maintenance Safety Rule
            if vehicle_id in vehicles_under_maintenance or vehicle_status == "MAINTENANCE":
                continue  # Exclude unsafe vehicles

            # 2. Driver Availability Factor (Max 35 pts)
            if driver_status in ["AVAILABLE", "ACTIVE", "IDLE"]:
                score += 35.0
                reasons.append("Driver is currently on-duty and available for immediate dispatch")
            elif driver_status == "ON_ROUTE":
                score += 15.0
                reasons.append("Driver is active on route; suitable for dynamic waypoint insertion")
            else:
                score += 0.0
                reasons.append(f"Driver status is {driver_status}")

            # 3. Vehicle Capacity Constraint & Fit (Max 25 pts)
            if vehicle_capacity < order_weight:
                continue  # Hard constraint: vehicle cannot carry the package weight

            capacity_utilization = order_weight / vehicle_capacity
            if capacity_utilization <= 0.8:
                score += 25.0
                reasons.append(f"Vehicle capacity ({vehicle_capacity:.0f} kg) comfortably accommodates order ({order_weight:.1f} kg)")
            else:
                score += 15.0
                reasons.append(f"Vehicle capacity ({vehicle_capacity:.0f} kg) is near load limit ({capacity_utilization*100:.0f}%)")

            # 4. Driver Proximity & Distance Efficiency (Max 25 pts)
            driver_lat = float(drv.get("current_latitude") or drv.get("lat") or depot_lat)
            driver_lng = float(drv.get("current_longitude") or drv.get("lng") or depot_lng)

            dist_to_pickup = haversine_distance(driver_lat, driver_lng, depot_lat, depot_lng)
            if dist_to_pickup < 5.0:
                score += 25.0
                reasons.append(f"Driver is at or very close to depot pickup point ({dist_to_pickup:.1f} km)")
            elif dist_to_pickup < 15.0:
                score += 18.0
                reasons.append(f"Driver is in operational vicinity of depot ({dist_to_pickup:.1f} km)")
            elif dist_to_pickup < 35.0:
                score += 10.0
                reasons.append(f"Driver is within transit range ({dist_to_pickup:.1f} km)")
            else:
                score += 5.0
                reasons.append(f"Driver is {dist_to_pickup:.1f} km from depot")

            # 5. Vehicle Status Health Bonus (Max 15 pts)
            if vehicle_status in ["AVAILABLE", "ACTIVE"]:
                score += 15.0
                reasons.append("Vehicle passed all routine maintenance and readiness checks")
            else:
                score += 5.0

            total_score = min(100.0, round(score, 1))

            candidates.append({
                "order_id": order_id,
                "order_number": order.get("order_number") or f"ORD-{order_id[:8]}",
                "driver_id": driver_id,
                "driver_name": driver_name,
                "driver_status": driver_status,
                "vehicle_id": vehicle_id,
                "vehicle_name": vehicle_name,
                "vehicle_capacity_kg": vehicle_capacity,
                "score": total_score,
                "reasons": reasons,
                "model_name": self.MODEL_NAME,
                "model_version": self.MODEL_VERSION,
            })

        # Sort descending by compatibility score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates


dispatch_ai_engine = DispatchAIEngine()
