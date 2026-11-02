import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# Allow import from optimization folder
_ROOT_DIR = str(Path(__file__).resolve().parents[5])
_BACKEND_DIR = str(Path(__file__).resolve().parents[4])
for _p in [_ROOT_DIR, _BACKEND_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.route import Route, RouteStop, OptimizationJob
from app.models.order import Order
from app.models.warehouse import Warehouse
from app.models.customer import Customer
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.schemas.optimization import (
    OptimizeRequest,
    OptimizationResultResponse,
    OptimizationJobResponse,
    CreateRoutesFromOptimizationRequest,
)
from app.schemas.logistics import OptimizationRequest, OptimizationResult
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
    w_res = await db.execute(select(Warehouse).where(Warehouse.id == req.warehouse_id))
    warehouse = w_res.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Depot Warehouse not found")

    # 2. Fetch orders
    orders = []
    if req.order_ids:
        o_res = await db.execute(select(Order).where(Order.id.in_(req.order_ids)))
        orders = o_res.scalars().all()

    if not orders and req.order_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="None of the specified orders were found")

    # 3. Fetch drivers & vehicles
    if req.driver_ids:
        d_res = await db.execute(select(Driver).where(Driver.id.in_(req.driver_ids)))
        drivers = d_res.scalars().all()
    else:
        d_res = await db.execute(select(Driver).where(Driver.status.in_(["AVAILABLE", "ASSIGNED"])))
        drivers = d_res.scalars().all()

    if req.vehicle_ids:
        v_res = await db.execute(select(Vehicle).where(Vehicle.id.in_(req.vehicle_ids)))
        vehicles = v_res.scalars().all()
    else:
        v_res = await db.execute(select(Vehicle))
        vehicles = v_res.scalars().all()

    prepared_vehicles = [
        {
            "id": v.id,
            "capacity": float(v.capacity or 1000.0),
            "vehicle_number": v.vehicle_number,
            "driver_id": v.driver_id,
        }
        for v in vehicles
    ]
    if not prepared_vehicles:
        prepared_vehicles = [{"id": "veh-default", "capacity": 500.0, "vehicle_number": "FLEET-01", "driver_id": None}]

    prepared_drivers = [
        {
            "id": d.id,
            "name": f"Driver {d.license_number}",
            "license_number": d.license_number,
            "status": d.status or "AVAILABLE",
        }
        for d in drivers
    ]

    cust_ids = [o.customer_id for o in orders if o.customer_id]
    custs_map = {}
    if cust_ids:
        c_res = await db.execute(select(Customer.id, Customer.name).where(Customer.id.in_(cust_ids)))
        custs_map = dict(c_res.all())

    prepared_orders = []
    for o in orders:
        tw_start = o.delivery_window_start
        tw_end = o.delivery_window_end
        tw_start_sec = int(tw_start.hour * 3600 + tw_start.minute * 60) if isinstance(tw_start, datetime) else 0
        tw_end_sec = int(tw_end.hour * 3600 + tw_end.minute * 60) if isinstance(tw_end, datetime) else 86400

        prepared_orders.append({
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": custs_map.get(o.customer_id, "Client"),
            "lat": o.delivery_latitude,
            "lng": o.delivery_longitude,
            "weight": o.package_weight,
            "priority": o.priority,
            "time_window_start_sec": tw_start_sec,
            "time_window_end_sec": tw_end_sec,
        })

    warehouse_dict = {
        "id": warehouse.id,
        "name": warehouse.name,
        "latitude": warehouse.latitude,
        "longitude": warehouse.longitude,
    }

    optimizer = RouteOptimizer()
    result = optimizer.optimize_dispatch(
        warehouse=warehouse_dict,
        orders=prepared_orders,
        vehicles=prepared_vehicles,
        drivers=prepared_drivers,
        max_route_distance_km=req.max_route_distance_km or 250.0,
        average_speed_kmh=req.average_speed_kmh or 40.0,
        time_limit_seconds=req.time_limit_seconds or 5,
    )

    now = datetime.utcnow()
    parameters_dict = {
        "warehouse_id": req.warehouse_id,
        "order_ids": req.order_ids,
        "driver_ids": req.driver_ids,
        "vehicle_ids": req.vehicle_ids,
    }

    db_job = OptimizationJob(
        id=result["job_id"],
        status="COMPLETED",
        parameters=parameters_dict,
        result=result,
        optimization_score=result["optimization_score"],
        total_distance_km=result["total_distance_km"],
        total_duration_min=result["total_duration_min"],
        created_at=now,
        updated_at=now,
    )
    db.add(db_job)
    await db.commit()

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
    res = await db.execute(select(OptimizationJob).where(OptimizationJob.id == job_id))
    job = res.scalar_one_or_none()
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
    res = await db.execute(select(OptimizationJob).where(OptimizationJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization Job not found")

    result = job.result or {}
    routes_data = result.get("routes", [])
    if not routes_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid routes found in optimization result")

    warehouse_id = job.parameters.get("warehouse_id") if job.parameters else None
    created_routes = []
    now = datetime.utcnow()

    for r_item in routes_data:
        veh_id = r_item.get("vehicle_id")
        if req.selected_vehicle_ids and veh_id not in req.selected_vehicle_ids:
            continue

        v_res = await db.execute(select(Vehicle).where(Vehicle.id == veh_id))
        vehicle = v_res.scalar_one_or_none()

        driver_id = r_item.get("driver_id")
        if not driver_id and vehicle:
            driver_id = vehicle.driver_id

        route_id = f"rt-{uuid.uuid4().hex[:6]}"
        route_name = f"Route - {r_item.get('vehicle_name', 'Fleet Vehicle')} ({r_item.get('stops_count', 0)} stops)"

        new_route = Route(
            id=route_id,
            name=route_name,
            driver_id=driver_id,
            vehicle_id=veh_id if vehicle else None,
            warehouse_id=warehouse_id,
            total_distance=r_item.get("total_distance_km", 0.0),
            estimated_duration=r_item.get("estimated_duration_min", 0.0),
            optimization_score=result.get("optimization_score", 100.0),
            status="PLANNED",
            created_at=now,
            started_at=None,
            completed_at=None,
        )
        db.add(new_route)

        for s_idx, stop_item in enumerate(r_item.get("stops", [])):
            if stop_item.get("stop_type") == "DEPOT":
                continue

            ord_id = stop_item.get("order_id")
            est_arrival = now + timedelta(minutes=stop_item.get("estimated_arrival_minutes", 0))

            stop_id = f"stp-{uuid.uuid4().hex[:6]}"
            new_stop = RouteStop(
                id=stop_id,
                route_id=route_id,
                order_id=ord_id,
                sequence=stop_item.get("sequence", s_idx),
                estimated_arrival=est_arrival,
                actual_arrival=None,
                status="PENDING",
                created_at=now,
            )
            db.add(new_stop)

            if ord_id:
                await db.execute(
                    update(Order)
                    .where(Order.id == ord_id)
                    .values(
                        status="ASSIGNED",
                        assigned_driver_id=driver_id,
                        updated_at=now,
                    )
                )

        created_routes.append(route_id)

    await db.commit()

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
