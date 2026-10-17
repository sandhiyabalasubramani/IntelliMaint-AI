"""
IntelliMaint AI — Maintenance Work Orders Router
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
)
from backend.app.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["Maintenance Planner"])


@router.get("", response_model=List[MaintenanceResponse])
def list_maintenance_tasks(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    status: Optional[str] = Query(None, description="Filter by status (Open, In Progress, Completed, Cancelled)"),
    priority: Optional[str] = Query(None, description="Filter by priority (Low, Medium, High, Critical)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve all maintenance work orders with optional filtering."""
    return MaintenanceService.get_tasks(
        db, machine_id=machine_id, status_filter=status, priority_filter=priority, skip=skip, limit=limit
    )


@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_task(
    task_in: MaintenanceCreate,
    db: Session = Depends(get_db),
):
    """Create a new maintenance work order."""
    return MaintenanceService.create_task(db, task_in)


@router.get("/{task_id}", response_model=MaintenanceResponse)
def get_maintenance_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a single maintenance work order by internal ID or Work Order Number."""
    return MaintenanceService.update_task(db, task_id, MaintenanceUpdate())


@router.patch("/{task_id}", response_model=MaintenanceResponse)
def update_maintenance_task(
    task_id: str,
    task_in: MaintenanceUpdate,
    db: Session = Depends(get_db),
):
    """Update maintenance task status, technician, priority, or completion notes."""
    return MaintenanceService.update_task(db, task_id, task_in)
