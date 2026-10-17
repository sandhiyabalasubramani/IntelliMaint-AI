"""
IntelliMaint AI — Database Layer & Persistence Tests
"""

import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.models.machine import Machine
from backend.app.models.telemetry import TelemetryRecord
from backend.app.models.prediction import PredictionRecord
from backend.app.models.maintenance import MaintenanceTask
from backend.app.schemas.machine import MachineCreate, MachineUpdate
from backend.app.services.machine_service import MachineService


def test_database_table_creation(db_session):
    """Test 2: Verify all expected tables exist in the metadata."""
    tables = db_session.get_bind().dialect.get_table_names(db_session.connection())
    assert "machines" in tables
    assert "telemetry_records" in tables
    assert "predictions" in tables
    assert "maintenance_tasks" in tables


def test_machine_creation_and_retrieval(db_session):
    """Test 3: Verify machine asset creation and retrieval by machine_id."""
    m_in = MachineCreate(
        machine_id="LATHE-TEST-99",
        name="Precision Test Lathe",
        machine_type="CNC Turning Center",
        department="Test Bay",
        manufacturer="Mazak",
        operational_status="OPERATIONAL",
    )
    created = MachineService.create_machine(db_session, m_in)
    assert created.id is not None
    assert created.machine_id == "LATHE-TEST-99"

    retrieved = MachineService.get_machine_by_id(db_session, "LATHE-TEST-99")
    assert retrieved is not None
    assert retrieved.name == "Precision Test Lathe"
    assert retrieved.operational_status == "OPERATIONAL"


def test_duplicate_machine_identifier_rejected(db_session, sample_machine):
    """Test 4: Enforce uniqueness on machine_id constraint."""
    duplicate = Machine(
        machine_id=sample_machine.machine_id,
        name="Duplicate Machine",
        machine_type="Lathe",
        operational_status="OPERATIONAL",
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_machine_update(db_session, sample_machine):
    """Verify machine parameters can be updated."""
    update_in = MachineUpdate(
        name="Updated 5-Axis Mill",
        operational_status="MAINTENANCE",
        notes="Spindle rebuild in progress",
    )
    updated = MachineService.update_machine(db_session, sample_machine.machine_id, update_in)
    assert updated.name == "Updated 5-Axis Mill"
    assert updated.operational_status == "MAINTENANCE"
    assert updated.notes == "Spindle rebuild in progress"


def test_cascade_delete_machine(db_session, sample_machine):
    """Test 23: Deleting a machine cascades to its telemetry and maintenance records."""
    # Add telemetry and task
    telem = TelemetryRecord(
        machine_id=sample_machine.machine_id,
        air_temperature=300.0,
        process_temperature=310.0,
        rotational_speed=1500.0,
        torque=40.0,
        tool_wear=30.0,
    )
    task = MaintenanceTask(
        work_order_no="WO-TEST-001",
        machine_id=sample_machine.machine_id,
        title="Check Spindle",
        priority="Medium",
        status="Open",
    )
    db_session.add(telem)
    db_session.add(task)
    db_session.commit()

    # Verify records exist
    assert db_session.query(TelemetryRecord).filter_by(machine_id=sample_machine.machine_id).count() == 1
    assert db_session.query(MaintenanceTask).filter_by(machine_id=sample_machine.machine_id).count() == 1

    # Delete machine
    MachineService.delete_machine(db_session, sample_machine.machine_id)

    # Verify cascaded removal
    assert db_session.query(Machine).filter_by(machine_id=sample_machine.machine_id).first() is None
    assert db_session.query(TelemetryRecord).filter_by(machine_id=sample_machine.machine_id).count() == 0
    assert db_session.query(MaintenanceTask).filter_by(machine_id=sample_machine.machine_id).count() == 0


def test_prediction_persistence(db_session, sample_machine):
    """Test 16: Verify prediction record persists accurately in database."""
    pred = PredictionRecord(
        prediction_id="PRED-TEST-1234",
        machine_id=sample_machine.machine_id,
        failure_probability=0.742,
        predicted_failure=1,
        risk_category="High",
        model_version="1.0.0",
        model_algorithm="Gradient Boosting",
        contributing_factors='[{"factor": "Critical Wear"}]',
        suggested_actions='["Replace Tool Insert"]',
        input_telemetry='{"tool_wear": 220}',
    )
    db_session.add(pred)
    db_session.commit()

    fetched = db_session.query(PredictionRecord).filter_by(prediction_id="PRED-TEST-1234").first()
    assert fetched is not None
    assert fetched.failure_probability == pytest.approx(0.742, rel=1e-3)
    assert fetched.risk_category == "High"
    assert fetched.predicted_failure == 1
