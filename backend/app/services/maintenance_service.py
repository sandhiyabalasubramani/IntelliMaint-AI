"""
IntelliMaint AI — Maintenance Work Order Service
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.maintenance import MaintenanceTask
from backend.app.models.machine import Machine
from backend.app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    VALID_STATUS_TRANSITIONS,
)


class MaintenanceService:
    @staticmethod
    def get_tasks(
        db: Session,
        machine_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MaintenanceTask]:
        query = db.query(MaintenanceTask)
        if machine_id:
            query = query.filter(MaintenanceTask.machine_id == machine_id)
        if status_filter:
            query = query.filter(MaintenanceTask.status == status_filter)
        if priority_filter:
            query = query.filter(MaintenanceTask.priority == priority_filter)
        return query.order_by(MaintenanceTask.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[MaintenanceTask]:
        return db.query(MaintenanceTask).filter(MaintenanceTask.id == task_id).first()

    @staticmethod
    def get_task_by_work_order_no(db: Session, work_order_no: str) -> Optional[MaintenanceTask]:
        return db.query(MaintenanceTask).filter(MaintenanceTask.work_order_no == work_order_no).first()

    @staticmethod
    def create_task(db: Session, task_in: MaintenanceCreate) -> MaintenanceTask:
        # Check machine exists or create fallback
        machine = db.query(Machine).filter(Machine.machine_id == task_in.machine_id).first()
        if not machine:
            machine = Machine(
                machine_id=task_in.machine_id,
                name=f"Machine {task_in.machine_id}",
                machine_type="CNC Milling Machine",
                operational_status="OPERATIONAL",
            )
            db.add(machine)
            db.commit()

        # Generate unique work order number
        year = datetime.now(timezone.utc).year
        random_suffix = uuid.uuid4().hex[:4].upper()
        wo_no = f"WO-{year}-{random_suffix}"

        task = MaintenanceTask(
            work_order_no=wo_no,
            machine_id=task_in.machine_id,
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            technician=task_in.technician,
            due_date=task_in.due_date,
            status=task_in.status,
            notes=task_in.notes,
            completed_at=datetime.now(timezone.utc) if task_in.status == "Completed" else None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, task_id_or_no: str | int, task_in: MaintenanceUpdate) -> MaintenanceTask:
        if isinstance(task_id_or_no, int) or (isinstance(task_id_or_no, str) and task_id_or_no.isdigit()):
            task = MaintenanceService.get_task_by_id(db, int(task_id_or_no))
        else:
            task = MaintenanceService.get_task_by_work_order_no(db, str(task_id_or_no))

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Maintenance task '{task_id_or_no}' not found.",
            )

        update_data = task_in.model_dump(exclude_unset=True)

        # Validate status transition if status is being updated
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            current_status = task.status
            allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [current_status])
            if new_status not in allowed_transitions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Invalid status transition from '{current_status}' to '{new_status}'. "
                        f"Allowed transitions: {allowed_transitions}"
                    ),
                )

            # Auto-manage completed_at timestamp
            if new_status == "Completed" and task.status != "Completed":
                task.completed_at = datetime.now(timezone.utc)
            elif new_status != "Completed":
                task.completed_at = None

        for field, value in update_data.items():
            setattr(task, field, value)

        db.commit()
        db.refresh(task)
        return task
