"""
IntelliMaint AI — Maintenance Work Order Lifecycle Tests
"""

import pytest
from fastapi import HTTPException
from backend.app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from backend.app.services.maintenance_service import MaintenanceService


def test_maintenance_task_creation_and_retrieval(db_session, sample_machine):
    """Test 17: Create a maintenance work order and retrieve it by work_order_no."""
    task_in = MaintenanceCreate(
        machine_id=sample_machine.machine_id,
        title="Check Spindle Runout",
        description="Inspect cutting vibration",
        priority="High",
        technician="Alex Mercer",
        status="Open",
    )
    created = MaintenanceService.create_task(db_session, task_in)
    assert created.id is not None
    assert created.work_order_no.startswith("WO-")
    assert created.status == "Open"
    assert created.completed_at is None

    retrieved = MaintenanceService.get_task_by_work_order_no(db_session, created.work_order_no)
    assert retrieved is not None
    assert retrieved.title == "Check Spindle Runout"


def test_valid_maintenance_status_transitions(db_session, sample_machine):
    """Test 17: Open -> In Progress -> Completed lifecycle transitions successfully."""
    task_in = MaintenanceCreate(
        machine_id=sample_machine.machine_id,
        title="Replace Coolant Pump Seal",
        priority="Medium",
        status="Open",
    )
    task = MaintenanceService.create_task(db_session, task_in)

    # 1. Transition Open -> In Progress
    step1 = MaintenanceService.update_task(
        db_session, task.work_order_no, MaintenanceUpdate(status="In Progress")
    )
    assert step1.status == "In Progress"
    assert step1.completed_at is None

    # 2. Transition In Progress -> Completed
    step2 = MaintenanceService.update_task(
        db_session, task.work_order_no, MaintenanceUpdate(status="Completed", notes="New Viton seal installed")
    )
    assert step2.status == "Completed"
    assert step2.completed_at is not None
    assert step2.notes == "New Viton seal installed"


def test_invalid_maintenance_status_transitions(db_session, sample_machine):
    """Test 18: Invalid status transitions raise HTTP 400 Bad Request."""
    task_in = MaintenanceCreate(
        machine_id=sample_machine.machine_id,
        title="Inspect Drive Belt",
        status="Open",
    )
    task = MaintenanceService.create_task(db_session, task_in)

    # Transitioning directly from Open to Completed is invalid
    with pytest.raises(HTTPException) as exc:
        MaintenanceService.update_task(
            db_session, task.work_order_no, MaintenanceUpdate(status="Completed")
        )
    assert exc.value.status_code == 400
    assert "Invalid status transition" in exc.value.detail
