import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db, check_db_connection
from app.api.deps import require_manager
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver
from app.models.maintenance import VehicleMaintenance, MaintenanceType, MaintenanceStatus
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceListResponse,
    MaintenanceVehicleDue,
    MaintenanceSummaryResponse,
)
from app.core.logistics_store import (
    SEED_VEHICLES,
    SEED_DRIVERS,
    SEED_VEHICLE_MAINTENANCE,
)
from app.services.audit_service import audit_service

router = APIRouter()


def _format_maintenance_record(rec: dict) -> dict:
    veh_id = rec.get("vehicle_id")
    veh = SEED_VEHICLES.get(veh_id, {})
    v_num = veh.get("vehicle_number") or veh.get("license_plate") or "UNKNOWN"
    v_type = veh.get("vehicle_type") or "VAN"

    m_type = rec.get("maintenance_type")
    if hasattr(m_type, "value"):
        m_type = m_type.value
    m_stat = rec.get("status")
    if hasattr(m_stat, "value"):
        m_stat = m_stat.value

    return {
        "id": rec["id"],
        "vehicle_id": veh_id,
        "maintenance_type": m_type or MaintenanceType.GENERAL_INSPECTION.value,
        "maintenance_date": rec.get("maintenance_date") or datetime.utcnow(),
        "mileage": float(rec.get("mileage") or 0.0),
        "notes": rec.get("notes"),
        "next_maintenance_mileage": float(rec.get("next_maintenance_mileage") or 0.0),
        "cost": float(rec.get("cost") or 0.0),
        "status": m_stat or MaintenanceStatus.COMPLETED.value,
        "created_at": rec.get("created_at") or datetime.utcnow(),
        "updated_at": rec.get("updated_at") or datetime.utcnow(),
        "vehicle_number": v_num,
        "vehicle_type": v_type,
    }


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
    if await check_db_connection():
        try:
            stmt = select(VehicleMaintenance).options(selectinload(VehicleMaintenance.vehicle)).order_by(desc(VehicleMaintenance.maintenance_date))
            if vehicle_id:
                stmt = stmt.where(VehicleMaintenance.vehicle_id == vehicle_id)
            if maintenance_type:
                stmt = stmt.where(VehicleMaintenance.maintenance_type == maintenance_type)
            if status:
                stmt = stmt.where(VehicleMaintenance.status == status)

            result = await db.execute(stmt)
            records = result.scalars().all()
            if records:
                out = []
                for r in records:
                    d = {
                        "id": r.id,
                        "vehicle_id": r.vehicle_id,
                        "maintenance_type": r.maintenance_type,
                        "maintenance_date": r.maintenance_date,
                        "mileage": r.mileage,
                        "notes": r.notes,
                        "next_maintenance_mileage": r.next_maintenance_mileage,
                        "cost": r.cost,
                        "status": r.status,
                        "created_at": r.created_at,
                        "updated_at": r.updated_at,
                        "vehicle_number": r.vehicle.vehicle_number if r.vehicle else "UNKNOWN",
                        "vehicle_type": r.vehicle.vehicle_type if r.vehicle else "VAN",
                    }
                    out.append(d)
                return out
        except Exception:
            pass

    records = list(SEED_VEHICLE_MAINTENANCE.values())
    if vehicle_id:
        records = [r for r in records if r.get("vehicle_id") == vehicle_id]
    if maintenance_type:
        records = [r for r in records if r.get("maintenance_type") == maintenance_type or getattr(r.get("maintenance_type"), "value", None) == maintenance_type]
    if status:
        records = [r for r in records if r.get("status") == status or getattr(r.get("status"), "value", None) == status]

    records.sort(key=lambda x: x.get("maintenance_date") or datetime.min, reverse=True)
    return [_format_maintenance_record(r) for r in records]


@router.get("/dashboard/summary", response_model=MaintenanceSummaryResponse)
async def get_maintenance_dashboard_summary(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated maintenance analytics, total spend, fleet health rating, and overdue count.
    """
    all_records = list(SEED_VEHICLE_MAINTENANCE.values())
    completed_count = sum(1 for r in all_records if r.get("status") in ["COMPLETED", MaintenanceStatus.COMPLETED])
    scheduled_count = sum(1 for r in all_records if r.get("status") in ["SCHEDULED", MaintenanceStatus.SCHEDULED, "IN_PROGRESS", MaintenanceStatus.IN_PROGRESS])
    total_cost = sum(float(r.get("cost") or 0.0) for r in all_records)

    by_type = {}
    for r in all_records:
        t = r.get("maintenance_type")
        if hasattr(t, "value"):
            t = t.value
        t_str = str(t)
        by_type[t_str] = by_type.get(t_str, 0) + 1

    # Calculate overdue & due soon vehicles
    overdue_count = 0
    due_soon_count = 0
    total_vehicles = max(len(SEED_VEHICLES), 1)

    for veh_id, veh in SEED_VEHICLES.items():
        curr_m = float(veh.get("mileage") or 0.0)
        # Find next maintenance
        highest_next = 0.0
        for r in all_records:
            if r.get("vehicle_id") == veh_id and r.get("status") in ["COMPLETED", MaintenanceStatus.COMPLETED]:
                nm = float(r.get("next_maintenance_mileage") or 0.0)
                if nm > highest_next:
                    highest_next = nm

        if highest_next > 0:
            if curr_m >= highest_next or veh.get("status") == "MAINTENANCE":
                overdue_count += 1
            elif highest_next - curr_m <= 1000:
                due_soon_count += 1

    # Fleet health score (100 - penalties for overdue & unmaintained vehicles)
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
    results: List[MaintenanceVehicleDue] = []

    for veh_id, veh in SEED_VEHICLES.items():
        curr_m = float(veh.get("mileage") or 0.0)
        v_num = veh.get("vehicle_number") or veh.get("license_plate") or "UNKNOWN"
        v_type = veh.get("vehicle_type") or "VAN"
        driver_id = veh.get("driver_id")
        driver_name = None
        if driver_id and driver_id in SEED_DRIVERS:
            driver_name = SEED_DRIVERS[driver_id].get("name") or f"Driver {SEED_DRIVERS[driver_id]['license_number']}"

        # Find latest completed maintenance record
        vehicle_records = [r for r in SEED_VEHICLE_MAINTENANCE.values() if r.get("vehicle_id") == veh_id]
        vehicle_records.sort(key=lambda x: x.get("maintenance_date") or datetime.min, reverse=True)

        last_date = None
        last_mileage = None
        next_mileage = curr_m + 5000.0  # Default next if no prior log

        if vehicle_records:
            latest = vehicle_records[0]
            last_date = latest.get("maintenance_date")
            last_mileage = float(latest.get("mileage") or 0.0)
            if latest.get("next_maintenance_mileage"):
                next_mileage = float(latest["next_maintenance_mileage"])

        is_overdue = curr_m >= next_mileage or veh.get("status") == "MAINTENANCE"
        mileage_overdue = max(0.0, curr_m - next_mileage)

        results.append(
            MaintenanceVehicleDue(
                vehicle_id=veh_id,
                vehicle_number=v_num,
                vehicle_type=v_type,
                current_mileage=curr_m,
                last_maintenance_date=last_date,
                last_maintenance_mileage=last_mileage,
                next_maintenance_mileage=next_mileage,
                mileage_overdue=mileage_overdue,
                is_overdue=is_overdue,
                status=veh.get("status", "AVAILABLE"),
                assigned_driver_id=driver_id,
                assigned_driver_name=driver_name,
            )
        )

    # Sort overdue vehicles first
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
    # 1. Validate vehicle exists
    veh = SEED_VEHICLES.get(maint_in.vehicle_id)
    if not veh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle '{maint_in.vehicle_id}' not found",
        )

    # 2. Validate next maintenance mileage is greater than service mileage
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

    record_dict = {
        "id": new_id,
        "vehicle_id": maint_in.vehicle_id,
        "maintenance_type": m_type,
        "maintenance_date": maint_date,
        "mileage": maint_in.mileage,
        "notes": maint_in.notes,
        "next_maintenance_mileage": maint_in.next_maintenance_mileage,
        "cost": maint_in.cost,
        "status": m_stat,
        "created_at": now,
        "updated_at": now,
    }

    # Automatically update vehicle mileage if service mileage is higher
    if maint_in.mileage > float(veh.get("mileage", 0.0)):
        veh["mileage"] = maint_in.mileage
        veh["updated_at"] = now

    # If maintenance is IN_PROGRESS, set vehicle status to MAINTENANCE
    if m_stat == MaintenanceStatus.IN_PROGRESS.value:
        veh["status"] = VehicleStatus.MAINTENANCE.value
    elif m_stat == MaintenanceStatus.COMPLETED.value and veh.get("status") == VehicleStatus.MAINTENANCE.value:
        veh["status"] = VehicleStatus.AVAILABLE.value

    SEED_VEHICLE_MAINTENANCE[new_id] = record_dict

    if await check_db_connection():
        try:
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
        except Exception:
            pass

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

    return _format_maintenance_record(record_dict)


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
async def get_maintenance_record(
    maintenance_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single vehicle maintenance record (ADMIN and LOGISTICS_MANAGER only).
    """
    rec = SEED_VEHICLE_MAINTENANCE.get(maintenance_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )
    return _format_maintenance_record(rec)


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
    rec = SEED_VEHICLE_MAINTENANCE.get(maintenance_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    if maint_in.maintenance_type is not None:
        rec["maintenance_type"] = maint_in.maintenance_type.value if hasattr(maint_in.maintenance_type, "value") else str(maint_in.maintenance_type)
    if maint_in.maintenance_date is not None:
        rec["maintenance_date"] = maint_in.maintenance_date
    if maint_in.mileage is not None:
        rec["mileage"] = maint_in.mileage
    if maint_in.notes is not None:
        rec["notes"] = maint_in.notes
    if maint_in.next_maintenance_mileage is not None:
        rec["next_maintenance_mileage"] = maint_in.next_maintenance_mileage
    if maint_in.cost is not None:
        rec["cost"] = maint_in.cost
    if maint_in.status is not None:
        rec["status"] = maint_in.status.value if hasattr(maint_in.status, "value") else str(maint_in.status)

    rec["updated_at"] = datetime.utcnow()
    SEED_VEHICLE_MAINTENANCE[maintenance_id] = rec

    await audit_service.log_event(
        action="MAINTENANCE_UPDATE",
        user=current_user,
        resource_type="MAINTENANCE",
        resource_id=maintenance_id,
        success=True,
        details={
            "vehicle_id": rec.get("vehicle_id"),
            "status": rec.get("status"),
            "cost": rec.get("cost"),
        },
        db=db,
    )

    return _format_maintenance_record(rec)


@router.delete("/{maintenance_id}", status_code=status.HTTP_200_OK)
async def delete_maintenance_record(
    maintenance_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a vehicle maintenance record (ADMIN and LOGISTICS_MANAGER only).
    """
    if maintenance_id not in SEED_VEHICLE_MAINTENANCE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    del_rec = SEED_VEHICLE_MAINTENANCE[maintenance_id]
    del SEED_VEHICLE_MAINTENANCE[maintenance_id]

    await audit_service.log_event(
        action="MAINTENANCE_DELETE",
        user=current_user,
        resource_type="MAINTENANCE",
        resource_id=maintenance_id,
        success=True,
        details={"vehicle_id": del_rec.get("vehicle_id")},
        db=db,
    )

    return {"status": "success", "message": f"Maintenance record {maintenance_id} deleted"}
