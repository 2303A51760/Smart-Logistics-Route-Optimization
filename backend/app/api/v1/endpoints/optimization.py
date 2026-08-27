import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Allow import from optimization folder
_ROOT_DIR = str(Path(__file__).resolve().parents[5])
_BACKEND_DIR = str(Path(__file__).resolve().parents[4])
for _p in [_ROOT_DIR, _BACKEND_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.api.deps import get_current_user
from app.core.database import get_db, check_db_connection
from app.models.user import User, UserRole
from app.models.route import Route, RouteStop, RouteStatus, RouteStopStatus, OptimizationJob
from app.models.order import Order, OrderStatus
from app.schemas.optimization import (
    OptimizeRequest,
    OptimizationResultResponse,
    OptimizationJobResponse,
    CreateRoutesFromOptimizationRequest,
)
from app.schemas.logistics import OptimizationRequest, OptimizationResult
from app.core.logistics_store import (
    SEED_WAREHOUSES,
    SEED_ORDERS,
    SEED_DRIVERS,
    SEED_VEHICLES,
    SEED_OPTIMIZATION_JOBS,
    SEED_ROUTES,
    SEED_ROUTE_STOPS,
    SEED_CUSTOMERS,
)
from optimization.route_optimizer import RouteOptimizer
from optimization.vrp_solver import VRPSolver
from app.services.audit_service import audit_service

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResultResponse)
async def run_optimization(
    req: OptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run real multi-vehicle route optimization using Google OR-Tools with capacity and time windows."""
    # 1. Fetch warehouse
    warehouse = SEED_WAREHOUSES.get(req.warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Depot Warehouse not found")

    # 2. Fetch orders
    orders = []
    for oid in req.order_ids:
        if oid in SEED_ORDERS:
            orders.append(SEED_ORDERS[oid])

    if not orders and req.order_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="None of the specified orders were found")

    # 3. Fetch drivers & vehicles
    drivers = []
    if req.driver_ids:
        drivers = [SEED_DRIVERS[did] for did in req.driver_ids if did in SEED_DRIVERS]
    else:
        drivers = [d for d in SEED_DRIVERS.values() if d.get("status") in ["AVAILABLE", "ASSIGNED"]]

    vehicles = []
    if req.vehicle_ids:
        vehicles = [SEED_VEHICLES[vid] for vid in req.vehicle_ids if vid in SEED_VEHICLES]
    else:
        vehicles = list(SEED_VEHICLES.values())

    if not vehicles:
        vehicles = [{"id": "veh-default", "capacity": 500.0, "vehicle_number": "FLEET-01", "driver_id": None}]

    prepared_drivers = [
        {
            "id": d["id"],
            "name": f"Driver {d['license_number']}",
            "license_number": d["license_number"],
            "status": d.get("status", "AVAILABLE"),
        }
        for d in drivers
    ]

    prepared_orders = []
    for o in orders:
        tw_start = o.get("delivery_window_start")
        tw_end = o.get("delivery_window_end")
        tw_start_sec = int(tw_start.hour * 3600 + tw_start.minute * 60) if isinstance(tw_start, datetime) else 0
        tw_end_sec = int(tw_end.hour * 3600 + tw_end.minute * 60) if isinstance(tw_end, datetime) else 86400

        cust = SEED_CUSTOMERS.get(o.get("customer_id"))

        prepared_orders.append({
            "id": o["id"],
            "order_number": o["order_number"],
            "customer_name": cust["name"] if cust else "Client",
            "lat": o["delivery_latitude"],
            "lng": o["delivery_longitude"],
            "weight": o["package_weight"],
            "priority": o["priority"],
            "time_window_start_sec": tw_start_sec,
            "time_window_end_sec": tw_end_sec,
        })

    warehouse_dict = {
        "id": warehouse["id"],
        "name": warehouse["name"],
        "latitude": warehouse["latitude"],
        "longitude": warehouse["longitude"],
    }

    optimizer = RouteOptimizer()
    result = optimizer.optimize_dispatch(
        warehouse=warehouse_dict,
        orders=prepared_orders,
        vehicles=vehicles,
        drivers=prepared_drivers,
        max_route_distance_km=req.max_route_distance_km or 250.0,
        average_speed_kmh=req.average_speed_kmh or 40.0,
        time_limit_seconds=req.time_limit_seconds or 5,
    )

    now = datetime.utcnow()
    job_record = {
        "id": result["job_id"],
        "status": "COMPLETED",
        "parameters": {
            "warehouse_id": req.warehouse_id,
            "order_ids": req.order_ids,
            "driver_ids": req.driver_ids,
            "vehicle_ids": req.vehicle_ids,
        },
        "result": result,
        "optimization_score": result["optimization_score"],
        "total_distance_km": result["total_distance_km"],
        "total_duration_min": result["total_duration_min"],
        "created_at": now,
        "updated_at": now,
    }
    SEED_OPTIMIZATION_JOBS[result["job_id"]] = job_record

    # Attempt DB async commit if live database is connected
    if await check_db_connection():
        try:
            db_job = OptimizationJob(
                id=result["job_id"],
                status="COMPLETED",
                parameters=job_record["parameters"],
                result=result,
                optimization_score=result["optimization_score"],
                total_distance_km=result["total_distance_km"],
                total_duration_min=result["total_duration_min"],
            )
            db.add(db_job)
            await db.commit()
        except Exception:
            pass

    # Log audit event for route optimization
    await audit_service.log_event(
        action="ROUTE_OPTIMIZE",
        user=current_user,
        resource_type="ROUTE",
        resource_id=result["job_id"],
        success=True,
        details={
            "warehouse_id": req.warehouse_id,
            "orders_count": len(req.order_ids),
            "orders_assigned": result.get("orders_assigned", 0),
            "vehicles_used": result.get("vehicles_used", 0),
            "total_distance_km": result.get("total_distance_km", 0.0),
        },
        db=db,
    )

    return OptimizationResultResponse(**result)


@router.get("/jobs/{job_id}", response_model=OptimizationJobResponse)
async def get_optimization_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve optimization job details and stored results."""
    job = SEED_OPTIMIZATION_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization Job not found")
    return job


@router.post("/jobs/{job_id}/create-routes", status_code=status.HTTP_201_CREATED)
async def create_executable_routes_from_job(
    job_id: str,
    req: CreateRoutesFromOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert optimization solution into executable Route and RouteStop records."""
    job = SEED_OPTIMIZATION_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization Job not found")

    result = job.get("result", {})
    routes_data = result.get("routes", [])
    if not routes_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid routes found in optimization result")

    warehouse_id = job.get("parameters", {}).get("warehouse_id")
    created_routes = []
    now = datetime.utcnow()

    for r_item in routes_data:
        veh_id = r_item.get("vehicle_id")
        if req.selected_vehicle_ids and veh_id not in req.selected_vehicle_ids:
            continue

        vehicle = SEED_VEHICLES.get(veh_id)
        driver_id = r_item.get("driver_id")
        if not driver_id and vehicle:
            driver_id = vehicle.get("driver_id")

        route_id = f"rt-{uuid.uuid4().hex[:6]}"
        route_name = f"Route - {r_item.get('vehicle_name', 'Fleet Vehicle')} ({r_item.get('stops_count', 0)} stops)"

        new_route = {
            "id": route_id,
            "name": route_name,
            "driver_id": driver_id,
            "vehicle_id": veh_id if vehicle else None,
            "warehouse_id": warehouse_id,
            "total_distance": r_item.get("total_distance_km", 0.0),
            "estimated_duration": r_item.get("estimated_duration_min", 0.0),
            "optimization_score": result.get("optimization_score", 100.0),
            "status": "PLANNED",
            "created_at": now,
            "started_at": None,
            "completed_at": None,
        }
        SEED_ROUTES[route_id] = new_route

        for s_idx, stop_item in enumerate(r_item.get("stops", [])):
            if stop_item.get("stop_type") == "DEPOT":
                continue

            ord_id = stop_item.get("order_id")
            est_arrival = now + timedelta(minutes=stop_item.get("estimated_arrival_minutes", 0))

            stop_id = f"stp-{uuid.uuid4().hex[:6]}"
            new_stop = {
                "id": stop_id,
                "route_id": route_id,
                "order_id": ord_id,
                "sequence": stop_item.get("sequence", s_idx),
                "estimated_arrival": est_arrival,
                "actual_arrival": None,
                "status": "PENDING",
            }
            SEED_ROUTE_STOPS[stop_id] = new_stop

            # Update assigned order
            if ord_id and ord_id in SEED_ORDERS:
                SEED_ORDERS[ord_id]["status"] = "ASSIGNED"
                if driver_id:
                    SEED_ORDERS[ord_id]["assigned_driver_id"] = driver_id

        created_routes.append(route_id)

    return {
        "message": f"Successfully created {len(created_routes)} executable routes.",
        "route_ids": created_routes,
    }


@router.post("/solve", response_model=OptimizationResult)
async def solve_routing_problem(req: OptimizationRequest):
    """Backwards compatibility for legacy simple VRP solver endpoint."""
    solver = VRPSolver()
    result = solver.solve_vrp(
        depot={"id": "depot-1", "name": "Warehouse Depot", "lat": req.depot_lat, "lng": req.depot_lng},
        orders=[{"id": d, "lat": req.depot_lat + 0.01 * (i + 1), "lng": req.depot_lng + 0.01 * (i + 1), "weight_kg": 10.0} for i, d in enumerate(req.delivery_ids)],
        vehicles=[{"id": v, "capacity_kg": 500.0} for v in req.vehicle_ids],
    )
    return {
        "job_id": result["job_id"],
        "status": result["status"],
        "num_vehicles": result["vehicles_used"],
        "num_stops": result["orders_assigned"],
        "total_distance_km": result["total_distance_km"],
        "estimated_total_time_min": result["total_duration_min"],
        "routes": [
            {
                "vehicle_id": r["vehicle_id"],
                "distance_km": r["total_distance_km"],
                "estimated_time_min": r["estimated_duration_min"],
                "stops": [
                    {
                        "stop_number": s["sequence"],
                        "id": s["order_id"] or "depot",
                        "name": s["name"],
                        "lat": s["latitude"],
                        "lng": s["longitude"],
                        "demand_kg": s["demand_kg"],
                    }
                    for s in r["stops"]
                ],
            }
            for r in result["routes"]
        ],
    }
