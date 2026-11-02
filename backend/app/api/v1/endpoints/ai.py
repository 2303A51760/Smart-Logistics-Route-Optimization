import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_manager
from app.core.database import get_db
from app.core.rate_limiter import RateLimiter, check_rate_limit
from app.models.user import User
from app.models.order import Order
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.warehouse import Warehouse
from app.models.maintenance import VehicleMaintenance
from app.services.order_priority import order_priority_engine
from app.ml.delay_prediction import delay_predictor
from app.services.dispatch_ai import dispatch_ai_engine
from app.services.dynamic_routing import dynamic_routing_engine
from app.services.ai_service import ai_service
from app.services.audit_service import audit_service
from app.ml.demand.predictor import demand_forecast_service
from app.schemas.ai import (
    OrderPriorityResponse,
    OrderPriorityListResponse,
    DispatchRecommendationsResponse,
    DispatchRecommendationItem,
    DelayRiskRequest,
    DelayRiskResponse,
    RouteReoptimizationRequest,
    RouteReoptimizationResponse,
    OperationsSummaryResponse,
)
from app.schemas.forecast import DemandForecastResponse

logger = logging.getLogger(__name__)

router = APIRouter()

ai_rate_limiter = RateLimiter(requests_limit=120, window_seconds=60)
ai_heavy_limiter = RateLimiter(requests_limit=30, window_seconds=60)


def _order_to_dict(ord_obj: Order) -> Dict[str, Any]:
    priority_val = ord_obj.priority.value if hasattr(ord_obj.priority, "value") else str(ord_obj.priority or "MEDIUM")
    status_val = ord_obj.status.value if hasattr(ord_obj.status, "value") else str(ord_obj.status or "PENDING")
    start_sec = None
    end_sec = None
    if ord_obj.delivery_window_start:
        start_sec = ord_obj.delivery_window_start.hour * 3600 + ord_obj.delivery_window_start.minute * 60
    if ord_obj.delivery_window_end:
        end_sec = ord_obj.delivery_window_end.hour * 3600 + ord_obj.delivery_window_end.minute * 60
    return {
        "id": ord_obj.id,
        "order_number": ord_obj.order_number,
        "priority": priority_val,
        "status": status_val,
        "package_weight": float(ord_obj.package_weight or 5.0),
        "weight": float(ord_obj.package_weight or 5.0),
        "delivery_latitude": float(ord_obj.delivery_latitude or 0.0),
        "delivery_longitude": float(ord_obj.delivery_longitude or 0.0),
        "lat": float(ord_obj.delivery_latitude or 0.0),
        "lng": float(ord_obj.delivery_longitude or 0.0),
        "time_window_start_sec": start_sec,
        "time_window_end_sec": end_sec,
    }


def _driver_to_dict(drv_obj: Driver) -> Dict[str, Any]:
    status_val = drv_obj.status.value if hasattr(drv_obj.status, "value") else str(drv_obj.status or "AVAILABLE")
    name = drv_obj.user.name if (drv_obj.user and hasattr(drv_obj.user, "name")) else f"Driver {drv_obj.id[:6]}"
    return {
        "id": drv_obj.id,
        "name": name,
        "user_name": name,
        "status": status_val,
        "current_latitude": float(drv_obj.current_latitude or 40.7128),
        "current_longitude": float(drv_obj.current_longitude or -74.0060),
        "license_number": drv_obj.license_number,
    }


def _vehicle_to_dict(veh_obj: Vehicle) -> Dict[str, Any]:
    status_val = veh_obj.status.value if hasattr(veh_obj.status, "value") else str(veh_obj.status or "AVAILABLE")
    return {
        "id": veh_obj.id,
        "plate_number": veh_obj.vehicle_number,
        "model": veh_obj.vehicle_type,
        "capacity_kg": float(veh_obj.capacity or 500.0),
        "capacity": float(veh_obj.capacity or 500.0),
        "status": status_val,
        "assigned_driver_id": veh_obj.driver_id,
    }


def _warehouse_to_dict(wh_obj: Warehouse) -> Dict[str, Any]:
    return {
        "id": wh_obj.id,
        "name": wh_obj.name,
        "latitude": float(wh_obj.latitude or 40.7128),
        "longitude": float(wh_obj.longitude or -74.0060),
    }


def _maint_to_dict(m_obj: VehicleMaintenance) -> Dict[str, Any]:
    status_val = m_obj.status.value if hasattr(m_obj.status, "value") else str(m_obj.status or "SCHEDULED")
    return {
        "id": m_obj.id,
        "vehicle_id": m_obj.vehicle_id,
        "status": status_val,
    }


# ==============================================================================
# 1. ORDER PRIORITY ENDPOINTS
# ==============================================================================
@router.get("/order-priority/{order_id}", response_model=OrderPriorityResponse)
async def get_order_priority(
    order_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculates explainable AI priority score and classification for an order."""
    await check_rate_limit(request, ai_rate_limiter)

    res = await db.execute(
        select(Order).where(or_(Order.id == order_id, Order.order_number == order_id))
    )
    ord_obj = res.scalar_one_or_none()
    if not ord_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )

    target_order = _order_to_dict(ord_obj)
    result = order_priority_engine.calculate_priority_score(target_order)

    # Audit log
    await audit_service.log_event(
        action="AI_PRIORITY_CALCULATED",
        user=current_user,
        resource_type="order",
        resource_id=order_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
        details=f"Calculated priority score {result['score']} ({result['priority']})",
        db=db,
    )

    return OrderPriorityResponse(**result)


@router.get("/order-priority", response_model=OrderPriorityListResponse)
async def list_order_priorities(
    request: Request,
    priority: Optional[str] = Query(None, description="Filter by tier (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Lists prioritized orders with scores and factor breakdowns."""
    await check_rate_limit(request, ai_rate_limiter)

    res = await db.execute(select(Order))
    orders = res.scalars().all()

    results = []
    for ord_obj in orders:
        ord_dict = _order_to_dict(ord_obj)
        p_res = order_priority_engine.calculate_priority_score(ord_dict)
        if priority and p_res["priority"].upper() != priority.upper():
            continue
        results.append(OrderPriorityResponse(**p_res))

    results.sort(key=lambda x: x.score, reverse=True)
    return OrderPriorityListResponse(total=len(results), orders=results[:limit])


# ==============================================================================
# 2. AI DISPATCH RECOMMENDATIONS ENDPOINTS
# ==============================================================================
@router.get("/dispatch/recommendations", response_model=DispatchRecommendationsResponse)
async def get_dispatch_recommendations(
    request: Request,
    order_id: Optional[str] = Query(None, description="Target order ID"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Returns AI-ranked driver and vehicle assignments for dispatchers."""
    await check_rate_limit(request, ai_rate_limiter)

    target_orders = []
    if order_id:
        res = await db.execute(
            select(Order).where(or_(Order.id == order_id, Order.order_number == order_id))
        )
        ord_obj = res.scalar_one_or_none()
        if not ord_obj:
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
        target_orders.append(_order_to_dict(ord_obj))
    else:
        res = await db.execute(
            select(Order).where(Order.status.in_(["PENDING", "UNASSIGNED"]))
        )
        orders = res.scalars().all()
        if not orders:
            res_all = await db.execute(select(Order).limit(3))
            orders = res_all.scalars().all()
        target_orders = [_order_to_dict(o) for o in orders]

    drv_res = await db.execute(select(Driver).options(selectinload(Driver.user)))
    drivers_list = [_driver_to_dict(d) for d in drv_res.scalars().all()]

    veh_res = await db.execute(select(Vehicle))
    vehicles_list = [_vehicle_to_dict(v) for v in veh_res.scalars().all()]

    wh_res = await db.execute(select(Warehouse))
    warehouses_list = [_warehouse_to_dict(w) for w in wh_res.scalars().all()]

    maint_res = await db.execute(select(VehicleMaintenance))
    maint_list = [_maint_to_dict(m) for m in maint_res.scalars().all()]

    all_recommendations = []
    for ord_item in target_orders:
        recs = dispatch_ai_engine.rank_assignments_for_order(
            order=ord_item,
            drivers=drivers_list,
            vehicles=vehicles_list,
            warehouse=warehouses_list[0] if warehouses_list else None,
            maintenance_records=maint_list,
        )
        for r in recs:
            all_recommendations.append(DispatchRecommendationItem(**r))

    all_recommendations.sort(key=lambda x: x.score, reverse=True)

    await audit_service.log_event(
        action="AI_DISPATCH_RECOMMENDATION",
        user=current_user,
        resource_type="dispatch",
        resource_id=order_id or "batch",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
        details=f"Generated {len(all_recommendations)} assignment recommendations",
        db=db,
    )

    return DispatchRecommendationsResponse(
        recommendations=all_recommendations[:limit],
        total=len(all_recommendations),
    )


# ==============================================================================
# 3. DELIVERY DELAY RISK ENDPOINTS
# ==============================================================================
@router.post("/delay-risk", response_model=DelayRiskResponse)
async def predict_delay_risk_endpoint(
    req: DelayRiskRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Predicts delay probability and risk level from transit parameters."""
    await check_rate_limit(request, ai_rate_limiter)

    res = delay_predictor.predict_delay_risk(
        order_id=req.order_id,
        distance_km=req.distance_km,
        stops_count=req.stops_count or 1,
        hour_of_day=req.hour_of_day or 14,
        weather_factor=req.weather_factor or 1,
        traffic_index=req.traffic_index or 1.2,
        weight_kg=req.weight_kg or 5.0,
        deadline_minutes_remaining=req.deadline_minutes_remaining,
    )

    return DelayRiskResponse(**res)


@router.get("/delay-risk/order/{order_id}", response_model=DelayRiskResponse)
async def get_order_delay_risk(
    order_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates delivery delay risk for an existing order in the platform."""
    await check_rate_limit(request, ai_rate_limiter)

    res = await db.execute(
        select(Order).where(or_(Order.id == order_id, Order.order_number == order_id))
    )
    match = res.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

    res = delay_predictor.predict_delay_risk(
        order_id=str(match.id),
        distance_km=15.0,
        stops_count=2,
        weight_kg=float(match.package_weight or 5.0),
    )
    return DelayRiskResponse(**res)


# ==============================================================================
# 4. DEMAND FORECAST ENDPOINT
# ==============================================================================
@router.get("/demand-forecast", response_model=DemandForecastResponse)
async def get_ai_demand_forecast(
    request: Request,
    horizon: int = Query(7, description="Forecast horizon in days (1, 7, 14, 30)"),
    warehouse_id: Optional[str] = Query(None, description="Optional warehouse filter"),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Returns AI demand forecasts with uncertainty bounds."""
    await check_rate_limit(request, ai_rate_limiter)

    if horizon not in [1, 7, 14, 30]:
        raise HTTPException(status_code=400, detail="Allowed forecast horizons: 1, 7, 14, 30 days.")

    # 1-day horizon is mapped from 7-day single slice
    h_param = 7 if horizon == 1 else horizon
    fc = demand_forecast_service.forecast_demand(horizon=h_param, warehouse_id=warehouse_id)
    if horizon == 1:
        fc["forecast"] = fc["forecast"][:1]
        fc["horizon_days"] = 1

    await audit_service.log_event(
        action="AI_FORECAST_GENERATED",
        user=current_user,
        resource_type="forecast",
        resource_id=warehouse_id or "all",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
        details=f"Generated {horizon}-day demand forecast",
        db=db,
    )

    return DemandForecastResponse(**fc)


# ==============================================================================
# 5. DYNAMIC ROUTE RE-OPTIMIZATION ENDPOINT
# ==============================================================================
@router.post("/routes/{route_id}/reoptimize", response_model=RouteReoptimizationResponse)
async def reoptimize_route_endpoint(
    route_id: str,
    req: RouteReoptimizationRequest,
    request: Request,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates dynamic route re-optimization and generates time/fuel delta."""
    await check_rate_limit(request, ai_heavy_limiter)

    rt_res = await db.execute(select(Route).where(Route.id == route_id))
    rt_match = rt_res.scalar_one_or_none()
    dist = float(rt_match.total_distance or 55.0) if rt_match else 55.0
    duration = float(rt_match.estimated_duration or 95.0) if rt_match else 95.0

    wh_res = await db.execute(select(Warehouse))
    warehouses_list = [_warehouse_to_dict(w) for w in wh_res.scalars().all()]

    ord_res = await db.execute(select(Order).limit(4))
    orders_list = [_order_to_dict(o) for o in ord_res.scalars().all()]

    veh_res = await db.execute(select(Vehicle).limit(2))
    vehicles_list = [_vehicle_to_dict(v) for v in veh_res.scalars().all()]

    drv_res = await db.execute(select(Driver).options(selectinload(Driver.user)).limit(2))
    drivers_list = [_driver_to_dict(d) for d in drv_res.scalars().all()]

    eval_result = dynamic_routing_engine.evaluate_reoptimization(
        route_id=route_id,
        warehouse=warehouses_list[0] if warehouses_list else {},
        current_orders=orders_list,
        vehicles=vehicles_list,
        drivers=drivers_list,
        current_distance_km=dist,
        current_duration_minutes=duration,
        trigger_reason=req.trigger_reason,
    )

    await audit_service.log_event(
        action="AI_ROUTE_REOPTIMIZATION",
        user=current_user,
        resource_type="route",
        resource_id=route_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
        details=f"Evaluated route re-optimization: beneficial={eval_result['reoptimization_beneficial']}, time_saved={eval_result['estimated_time_saved_minutes']}m",
        db=db,
    )

    return RouteReoptimizationResponse(**eval_result)


# ==============================================================================
# 6. OPERATIONS SUMMARY ENDPOINT
# ==============================================================================
@router.get("/operations-summary", response_model=OperationsSummaryResponse)
async def get_operations_summary(
    request: Request,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregated executive operational intelligence and KPI metrics."""
    await check_rate_limit(request, ai_rate_limiter)

    summary_data = await ai_service.get_operations_summary(db=db)
    return OperationsSummaryResponse(**summary_data)
