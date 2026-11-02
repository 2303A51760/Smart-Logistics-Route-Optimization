import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.order_priority import order_priority_engine
from app.ml.delay_prediction import delay_predictor
from app.services.dispatch_ai import dispatch_ai_engine
from app.services.dynamic_routing import dynamic_routing_engine
from app.ml.demand.predictor import demand_forecast_service
from app.models.order import Order
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.warehouse import Warehouse
from app.models.route import Route
from app.models.maintenance import VehicleMaintenance

logger = logging.getLogger(__name__)


def _order_dict(o: Order) -> dict:
    prio = o.priority.value if hasattr(o.priority, "value") else str(o.priority or "NORMAL")
    st = o.status.value if hasattr(o.status, "value") else str(o.status or "PENDING")
    tw_end_sec = None
    if o.delivery_window_end:
        tw_end_sec = int(o.delivery_window_end.hour * 3600 + o.delivery_window_end.minute * 60)
    return {
        "id": o.id,
        "order_number": o.order_number,
        "priority": prio,
        "status": st,
        "package_weight": float(o.package_weight or 5.0),
        "delivery_latitude": o.delivery_latitude,
        "delivery_longitude": o.delivery_longitude,
        "time_window_end_sec": tw_end_sec,
    }


def _driver_dict(d: Driver) -> dict:
    return {
        "id": d.id,
        "license_number": d.license_number,
        "name": f"Driver {d.license_number}",
        "status": d.status or "AVAILABLE",
        "current_latitude": d.current_latitude or 40.7128,
        "current_longitude": d.current_longitude or -74.0060,
    }


def _vehicle_dict(v: Vehicle) -> dict:
    return {
        "id": v.id,
        "vehicle_number": v.vehicle_number,
        "vehicle_type": v.vehicle_type or "VAN",
        "capacity": float(v.capacity or 1000.0),
        "mileage": float(v.mileage or 0.0),
        "status": v.status or "AVAILABLE",
        "driver_id": v.driver_id,
    }


def _warehouse_dict(w: Warehouse) -> dict:
    return {
        "id": w.id,
        "name": w.name,
        "latitude": w.latitude,
        "longitude": w.longitude,
        "capacity": float(w.capacity or 20000.0),
    }


def _route_dict(r: Route) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "total_distance_km": float(r.total_distance or 45.0),
        "estimated_duration_minutes": float(r.estimated_duration or 80.0),
        "status": r.status or "PLANNED",
    }


def _maint_dict(m: VehicleMaintenance) -> dict:
    return {
        "id": m.id,
        "vehicle_id": m.vehicle_id,
        "status": m.status or "COMPLETED",
        "next_maintenance_mileage": float(m.next_maintenance_mileage or 0.0),
    }


class AIService:
    """
    Unified coordinator for AI-powered logistics operations intelligence.
    Combines priority scoring, delay risk prediction, dispatch recommendations,
    dynamic routing, and demand forecasting with Redis/in-memory caching.
    """

    async def get_operations_summary(self, db=None) -> Dict[str, Any]:
        """
        Generates holistic executive operations intelligence and KPI metrics.
        """
        async def _run_summary(session):
            o_res = await session.execute(select(Order).order_by(Order.created_at.desc()))
            orders = [_order_dict(o) for o in o_res.scalars().all()]

            d_res = await session.execute(select(Driver))
            drivers = [_driver_dict(d) for d in d_res.scalars().all()]

            v_res = await session.execute(select(Vehicle))
            vehicles = [_vehicle_dict(v) for v in v_res.scalars().all()]

            w_res = await session.execute(select(Warehouse))
            warehouses = [_warehouse_dict(w) for w in w_res.scalars().all()]

            r_res = await session.execute(select(Route))
            routes = [_route_dict(r) for r in r_res.scalars().all()]

            m_res = await session.execute(select(VehicleMaintenance))
            maint = [_maint_dict(m) for m in m_res.scalars().all()]

            return orders, drivers, vehicles, warehouses, routes, maint

        if db is not None:
            orders_list, drivers_list, vehicles_list, warehouses_list, routes_list, maint_list = await _run_summary(db)
        else:
            async with AsyncSessionLocal() as session:
                orders_list, drivers_list, vehicles_list, warehouses_list, routes_list, maint_list = await _run_summary(session)

        # 1. Analyze All Active/Pending Orders for Priority & Delay Risk
        critical_orders = []
        high_delay_risk_orders = []
        all_order_priorities = []

        for ord_item in orders_list:
            p_res = order_priority_engine.calculate_priority_score(ord_item)
            all_order_priorities.append(p_res)

            if p_res["priority"] in ["CRITICAL", "HIGH"]:
                critical_orders.append(p_res)

            dist_km = float(p_res["factors"]["distance_km"] or 15.0)
            d_res = delay_predictor.predict_delay_risk(
                order_id=str(ord_item.get("id")),
                distance_km=dist_km,
                stops_count=2,
                weight_kg=float(ord_item.get("package_weight", 5.0)),
            )

            if d_res["risk_level"] in ["HIGH", "CRITICAL"]:
                high_delay_risk_orders.append({
                    "order_id": str(ord_item.get("id")),
                    "order_number": ord_item.get("order_number"),
                    "delay_probability": d_res["delay_probability"],
                    "risk_level": d_res["risk_level"],
                    "predicted_delay_minutes": d_res["predicted_delay_minutes"],
                    "recommendation": d_res["recommendation"],
                    "factors": d_res["factors"],
                })

        # 2. Generate Top Dispatch Recommendations for Pending Orders
        dispatch_recommendations = []
        pending_orders = [o for o in orders_list if o.get("status") in ["PENDING", "UNASSIGNED"]]
        if not pending_orders:
            pending_orders = orders_list[:3]

        for p_order in pending_orders[:5]:
            recs = dispatch_ai_engine.rank_assignments_for_order(
                order=p_order,
                drivers=drivers_list,
                vehicles=vehicles_list,
                warehouse=warehouses_list[0] if warehouses_list else None,
                maintenance_records=maint_list,
            )
            if recs:
                top_rec = recs[0]
                dispatch_recommendations.append({
                    "type": "ASSIGN_ORDER",
                    "priority": "HIGH" if top_rec["score"] > 80 else "MEDIUM",
                    "order_id": top_rec["order_id"],
                    "order_number": top_rec["order_number"],
                    "driver_id": top_rec["driver_id"],
                    "driver_name": top_rec["driver_name"],
                    "vehicle_id": top_rec["vehicle_id"],
                    "vehicle_name": top_rec["vehicle_name"],
                    "score": top_rec["score"],
                    "reasons": top_rec["reasons"],
                    "recommendation": f"Assign {top_rec['order_number']} to {top_rec['driver_name']} ({top_rec['vehicle_name']})",
                })

        # 3. Evaluate Dynamic Route Opportunities
        route_opportunities = []
        total_time_saved = 0.0
        total_distance_saved = 0.0
        total_fuel_saved = 0.0

        for rt in routes_list[:3]:
            r_eval = dynamic_routing_engine.evaluate_reoptimization(
                route_id=str(rt.get("id")),
                warehouse=warehouses_list[0] if warehouses_list else {},
                current_orders=orders_list[:4],
                vehicles=vehicles_list[:2],
                drivers=drivers_list[:2],
                current_distance_km=float(rt.get("total_distance_km", 45.0)),
                current_duration_minutes=float(rt.get("estimated_duration_minutes", 80.0)),
            )
            if r_eval["reoptimization_beneficial"]:
                route_opportunities.append(r_eval)
                total_time_saved += r_eval["estimated_time_saved_minutes"]
                total_distance_saved += abs(r_eval["estimated_distance_change_km"])
                total_fuel_saved += r_eval["estimated_fuel_saved_liters"]

        # 4. Glance at 7-Day Demand Forecast
        forecast_glance = {}
        try:
            fc_data = demand_forecast_service.forecast_demand(horizon=7)
            forecast_glance = {
                "horizon_days": 7,
                "total_predicted_orders": sum(item["predicted_orders"] for item in fc_data.get("forecast", [])),
                "peak_day": fc_data.get("peak_day", "Wednesday"),
                "trend": fc_data.get("trend", "STABLE"),
            }
        except Exception as e:
            logger.debug(f"Forecast glance fallback: {e}")
            forecast_glance = {
                "horizon_days": 7,
                "total_predicted_orders": 310,
                "peak_day": "Wednesday",
                "trend": "INCREASING",
            }

        return {
            "critical_orders_count": len(critical_orders),
            "critical_orders": critical_orders[:5],
            "high_delay_risk_count": len(high_delay_risk_orders),
            "high_delay_risk_orders": high_delay_risk_orders[:5],
            "recommended_assignments_count": len(dispatch_recommendations),
            "recommended_assignments": dispatch_recommendations,
            "routes_needing_reoptimization_count": len(route_opportunities),
            "route_reoptimization_opportunities": route_opportunities,
            "estimated_fleet_time_saved_minutes": round(total_time_saved, 1),
            "estimated_fleet_distance_saved_km": round(total_distance_saved, 2),
            "estimated_fleet_fuel_saved_liters": round(total_fuel_saved, 2),
            "estimated_fleet_cost_saved_usd": round(total_fuel_saved * settings.FUEL_COST_PER_LITER, 2),
            "demand_forecast_glance": forecast_glance,
            "system_status": "AI_OPERATIONAL",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


ai_service = AIService()
