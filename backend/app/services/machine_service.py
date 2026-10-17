"""
IntelliMaint AI — Machine Service
"""

from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.machine import Machine
from backend.app.schemas.machine import MachineCreate, MachineUpdate


class MachineService:
    @staticmethod
    def get_all_machines(db: Session, skip: int = 0, limit: int = 100) -> List[Machine]:
        return db.query(Machine).offset(skip).limit(limit).all()

    @staticmethod
    def get_machine_by_id(db: Session, machine_id: str) -> Optional[Machine]:
        return db.query(Machine).filter(Machine.machine_id == machine_id).first()

    @staticmethod
    def create_machine(db: Session, machine_in: MachineCreate) -> Machine:
        existing = db.query(Machine).filter(Machine.machine_id == machine_in.machine_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Machine with ID '{machine_in.machine_id}' already exists in registry.",
            )

        machine = Machine(**machine_in.model_dump())
        db.add(machine)
        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def update_machine(db: Session, machine_id: str, machine_in: MachineUpdate) -> Machine:
        machine = MachineService.get_machine_by_id(db, machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine '{machine_id}' not found.",
            )

        update_data = machine_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(machine, field, value)

        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def delete_machine(db: Session, machine_id: str) -> bool:
        machine = MachineService.get_machine_by_id(db, machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine '{machine_id}' not found.",
            )

        db.delete(machine)
        db.commit()
        return True
