"""
IntelliMaint AI — Machine Registry Router
"""

from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.machine import (
    MachineCreate,
    MachineUpdate,
    MachineResponse,
)
from backend.app.services.machine_service import MachineService

router = APIRouter(prefix="/machines", tags=["Machine Registry"])


@router.get("", response_model=List[MachineResponse])
def list_machines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve all registered industrial machines in the fleet."""
    return MachineService.get_all_machines(db, skip=skip, limit=limit)


@router.post("", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def create_machine(
    machine_in: MachineCreate,
    db: Session = Depends(get_db),
):
    """Register a new industrial machine with unique machine ID."""
    return MachineService.create_machine(db, machine_in)


@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(
    machine_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific machine by unique ID."""
    machine = MachineService.get_machine_by_id(db, machine_id)
    if not machine:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine '{machine_id}' not found.",
        )
    return machine


@router.patch("/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: str,
    machine_in: MachineUpdate,
    db: Session = Depends(get_db),
):
    """Update machine parameters, operational status, or notes."""
    return MachineService.update_machine(db, machine_id, machine_in)


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(
    machine_id: str,
    db: Session = Depends(get_db),
):
    """Delete a machine from the registry and cascade related data."""
    MachineService.delete_machine(db, machine_id)
    return None
