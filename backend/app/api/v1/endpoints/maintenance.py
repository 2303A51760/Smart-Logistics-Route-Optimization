import uuid
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.api.deps import require_manager
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver
from app.models.maintenance import VehicleMaintenance, MaintenanceStatus
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceVehicleDue,
    MaintenanceSummaryResponse,
)
from app.services.audit_service import audit_service

router = APIRouter()


def _format_maintenance_row(r: VehicleMaintenance, v_num: str = "UNKNOWN", v_type: str = "VAN") -> MaintenanceResponse:
    return MaintenanceResponse(
        id=r.id,
        vehicle_id=r.vehicle_id,
        maintenance_type=r.maintenance_type,
        maintenance_date=r.maintenance_date or datetime.utcnow(),
        mileage=float(r.mileage or 0.0),
        notes=r.notes,
        next_maintenance_mileage=float(r.next_maintenance_mileage or 0.0),
        cost=float(r.cost or 0.0),
        status=r.status,
        created_at=r.created_at or datetime.utcnow(),
        updated_at=r.updated_at or datetime.utcnow(),
        vehicle_number=v_num,
        vehicle_type=v_type,
    )


@router.get("", response_model=List[MaintenanceResponse])
async def list_maintenance_records(
    vehicle_id: Optional[str] = None,
    maintenance_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    List all vehicle maintenance records (ADMIN and LOGISTICS_MANAGER only).
    Supports filtering by vehicle_id, maintenance_type, and status.
    """
    stmt = (
        select(VehicleMaintenance, Vehicle.vehicle_number, Vehicle.vehicle_type)
        .outerjoin(Vehicle, VehicleMaintenance.vehicle_id == Vehicle.id)
        .order_by(desc(VehicleMaintenance.maintenance_date))
    )
    if vehicle_id:
        stmt = stmt.where(VehicleMaintenance.vehicle_id == vehicle_id)
    if maintenance_type:
        stmt = stmt.where(VehicleMaintenance.maintenance_type == maintenance_type)
    if status:
        stmt = stmt.where(VehicleMaintenance.status == status)

    result = await db.execute(stmt)
    rows = result.all()

    return [_format_maintenance_row(r, v_num or "UNKNOWN", v_type or "VAN") for r, v_num, v_type in rows]


@router.get("/dashboard/summary", response_model=MaintenanceSummaryResponse)
async def get_maintenance_dashboard_summary(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated maintenance analytics, total spend, fleet health rating, and overdue count.
    """
    res = await db.execute(select(VehicleMaintenance))
    all_records = res.scalars().all()

    completed_count = sum(1 for r in all_records if r.status in ["COMPLETED", MaintenanceStatus.COMPLETED.value])
    scheduled_count = sum(1 for r in all_records if r.status in ["SCHEDULED", MaintenanceStatus.SCHEDULED.value, "IN_PROGRESS", MaintenanceStatus.IN_PROGRESS.value])
    total_cost = sum(float(r.cost or 0.0) for r in all_records)

    by_type: Dict[str, int] = {}
    for r in all_records:
        t_str = str(r.maintenance_type)
        by_type[t_str] = by_type.get(t_str, 0) + 1

    veh_res = await db.execute(select(Vehicle))
    vehicles = veh_res.scalars().all()

    overdue_count = 0
    due_soon_count = 0

    for veh in vehicles:
        curr_m = float(veh.mileage or 0.0)
        highest_next = 0.0
        for r in all_records:
            if r.vehicle_id == veh.id and r.status in ["COMPLETED", MaintenanceStatus.COMPLETED.value]:
                nm = float(r.next_maintenance_mileage or 0.0)
                if nm > highest_next:
                    highest_next = nm

        if highest_next > 0:
            if curr_m >= highest_next or veh.status == "MAINTENANCE":
                overdue_count += 1
            elif highest_next - curr_m <= 1000:
                due_soon_count += 1

    health_score = max(0.0, min(100.0, 100.0 - (overdue_count * 20.0) - (due_soon_count * 5.0)))

    return {
        "total_records": len(all_records),
        "completed_services": completed_count,
        "scheduled_services": scheduled_count,
        "total_maintenance_cost": round(total_cost, 2),
        "vehicles_overdue_count": overdue_count,
        "vehicles_due_soon_count": due_soon_count,
        "fleet_health_score": round(health_score, 1),
        "by_type": by_type,
    }


@router.get("/due", response_model=List[MaintenanceVehicleDue])
async def list_vehicles_due_for_maintenance(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    List all fleet vehicles that are currently due or overdue for scheduled service.
    """
    veh_res = await db.execute(select(Vehicle).order_by(Vehicle.created_at))
    vehicles = veh_res.scalars().all()

    driver_ids = [v.driver_id for v in vehicles if v.driver_id]
    drivers_map = {}
    if driver_ids:
        d_res = await db.execute(select(Driver.id, Driver.license_number).where(Driver.id.in_(driver_ids)))
        drivers_map = dict(d_res.all())

    results: List[MaintenanceVehicleDue] = []
    for veh in vehicles:
        curr_m = float(veh.mileage or 0.0)
        v_num = veh.vehicle_number or "UNKNOWN"
        v_type = veh.vehicle_type or "VAN"
        driver_id = veh.driver_id
        driver_name = f"Driver {drivers_map[driver_id]}" if driver_id and driver_id in drivers_map else None

        m_res = await db.execute(
            select(VehicleMaintenance)
            .where(VehicleMaintenance.vehicle_id == veh.id)
            .order_by(desc(VehicleMaintenance.maintenance_date))
        )
        vehicle_records = m_res.scalars().all()

        last_date = None
        last_mileage = None
        next_mileage = curr_m + 5000.0

        if vehicle_records:
            latest = vehicle_records[0]
            last_date = latest.maintenance_date
            last_mileage = float(latest.mileage or 0.0)
            if latest.next_maintenance_mileage:
                next_mileage = float(latest.next_maintenance_mileage)

        is_overdue = curr_m >= next_mileage or veh.status == "MAINTENANCE"
        mileage_overdue = max(0.0, curr_m - next_mileage)

        results.append(
            MaintenanceVehicleDue(
                vehicle_id=veh.id,
                vehicle_number=v_num,
                vehicle_type=v_type,
                current_mileage=curr_m,
                last_maintenance_date=last_date,
                last_maintenance_mileage=last_mileage,
                next_maintenance_mileage=next_mileage,
                mileage_overdue=mileage_overdue,
                is_overdue=is_overdue,
                status=veh.status or "AVAILABLE",
                assigned_driver_id=driver_id,
                assigned_driver_name=driver_name,
            )
        )

    results.sort(key=lambda x: (not x.is_overdue, -x.mileage_overdue))
    return results


@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_record(
    maint_in: MaintenanceCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Log or schedule a new vehicle maintenance record (ADMIN and LOGISTICS_MANAGER only).
    """
    v_res = await db.execute(select(Vehicle).where(Vehicle.id == maint_in.vehicle_id))
    veh = v_res.scalar_one_or_none()
    if not veh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle '{maint_in.vehicle_id}' not found",
        )

    if maint_in.next_maintenance_mileage <= maint_in.mileage:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Next maintenance mileage must be greater than current service mileage",
        )

    new_id = f"maint-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()
    maint_date = maint_in.maintenance_date or now

    m_type = maint_in.maintenance_type.value if hasattr(maint_in.maintenance_type, "value") else str(maint_in.maintenance_type)
    m_stat = maint_in.status.value if hasattr(maint_in.status, "value") else str(maint_in.status)

    if maint_in.mileage > float(veh.mileage or 0.0):
        veh.mileage = maint_in.mileage
        veh.updated_at = now

    if m_stat == MaintenanceStatus.IN_PROGRESS.value:
        veh.status = VehicleStatus.MAINTENANCE.value
    elif m_stat == MaintenanceStatus.COMPLETED.value and veh.status == VehicleStatus.MAINTENANCE.value:
        veh.status = VehicleStatus.AVAILABLE.value

    db_maint = VehicleMaintenance(
        id=new_id,
        vehicle_id=maint_in.vehicle_id,
        maintenance_type=m_type,
        maintenance_date=maint_date,
        mileage=maint_in.mileage,
        notes=maint_in.notes,
        next_maintenance_mileage=maint_in.next_maintenance_mileage,
        cost=maint_in.cost,
        status=m_stat,
        created_at=now,
        updated_at=now,
    )
    db.add(db_maint)
    await db.commit()
    await db.refresh(db_maint)

    await audit_service.log_event(
        action="MAINTENANCE_CREATE",
        user=current_user,
        resource_type="MAINTENANCE",
        resource_id=new_id,
        success=True,
        details={
            "vehicle_id": maint_in.vehicle_id,
            "maintenance_type": m_type,
            "status": m_stat,
            "cost": maint_in.cost,
        },
        db=db,
    )

    return _format_maintenance_row(db_maint, veh.vehicle_number, veh.vehicle_type)


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
async def get_maintenance_record(
    maintenance_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single vehicle maintenance record (ADMIN and LOGISTICS_MANAGER only).
    """
    stmt = (
        select(VehicleMaintenance, Vehicle.vehicle_number, Vehicle.vehicle_type)
        .outerjoin(Vehicle, VehicleMaintenance.vehicle_id == Vehicle.id)
        .where(VehicleMaintenance.id == maintenance_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )
    rec, v_num, v_type = row
    return _format_maintenance_row(rec, v_num or "UNKNOWN", v_type or "VAN")


@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
async def update_maintenance_record(
    maintenance_id: str,
    maint_in: MaintenanceUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a vehicle maintenance record (ADMIN and LOGISTICS_MANAGER only).
    """
    stmt = select(VehicleMaintenance).where(VehicleMaintenance.id == maintenance_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    if maint_in.maintenance_type is not None:
        rec.maintenance_type = maint_in.maintenance_type.value if hasattr(maint_in.maintenance_type, "value") else str(maint_in.maintenance_type)
    if maint_in.maintenance_date is not None:
        rec.maintenance_date = maint_in.maintenance_date
    if maint_in.mileage is not None:
        rec.mileage = maint_in.mileage
    if maint_in.notes is not None:
        rec.notes = maint_in.notes
    if maint_in.next_maintenance_mileage is not None:
        rec.next_maintenance_mileage = maint_in.next_maintenance_mileage
    if maint_in.cost is not None:
        rec.cost = maint_in.cost
    if maint_in.status is not None:
        rec.status = maint_in.status.value if hasattr(maint_in.status, "value") else str(maint_in.status)

    rec.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rec)

    v_res = await db.execute(select(Vehicle.vehicle_number, Vehicle.vehicle_type).where(Vehicle.id == rec.vehicle_id))
    v_info = v_res.first()
    v_num = v_info[0] if v_info else "UNKNOWN"
    v_type = v_info[1] if v_info else "VAN"

    await audit_service.log_event(
        action="MAINTENANCE_UPDATE",
        user=current_user,
        resource_type="MAINTENANCE",
        resource_id=maintenance_id,
        success=True,
        details={
            "vehicle_id": rec.vehicle_id,
            "status": rec.status,
            "cost": rec.cost,
        },
        db=db,
    )

    return _format_maintenance_row(rec, v_num, v_type)


@router.delete("/{maintenance_id}", status_code=status.HTTP_200_OK)
async def delete_maintenance_record(
    maintenance_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a vehicle maintenance record (ADMIN and LOGISTICS_MANAGER only).
    """
    stmt = select(VehicleMaintenance).where(VehicleMaintenance.id == maintenance_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    veh_id = rec.vehicle_id
    await db.delete(rec)
    await db.commit()

    await audit_service.log_event(
        action="MAINTENANCE_DELETE",
        user=current_user,
        resource_type="MAINTENANCE",
        resource_id=maintenance_id,
        success=True,
        details={"vehicle_id": veh_id},
        db=db,
    )

    return {"status": "success", "message": f"Maintenance record {maintenance_id} deleted"}
