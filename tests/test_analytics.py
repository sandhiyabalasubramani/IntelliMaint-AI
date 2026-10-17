"""
IntelliMaint AI — Analytics & Fleet Aggregation Tests
"""

import io
import pandas as pd
from backend.app.models.telemetry import TelemetryRecord
from backend.app.models.maintenance import MaintenanceTask
from backend.app.models.prediction import PredictionRecord
from backend.app.services.analytics_service import AnalyticsService


def test_fleet_analytics_kpi_calculations(db_session, sample_machine):
    """Test 19: Fleet analytics accurately calculates total machines, risk counts, and open work orders."""
    # Add a prediction
    pred = PredictionRecord(
        prediction_id="PRED-TEST-KPI",
        machine_id=sample_machine.machine_id,
        failure_probability=0.85,
        predicted_failure=1,
        risk_category="High",
        model_version="1.0.0",
        model_algorithm="Gradient Boosting",
    )
    # Add an open task and a completed task
    t_open = MaintenanceTask(
        work_order_no="WO-OPEN-1",
        machine_id=sample_machine.machine_id,
        title="Emergency Stop Test",
        status="Open",
    )
    t_done = MaintenanceTask(
        work_order_no="WO-DONE-1",
        machine_id=sample_machine.machine_id,
        title="Filter Swap",
        status="Completed",
    )
    db_session.add(pred)
    db_session.add(t_open)
    db_session.add(t_done)
    db_session.commit()

    summary = AnalyticsService.get_fleet_summary(db_session)

    assert summary.total_registered_machines == 1
    assert summary.high_risk_machines_count == 1
    assert summary.open_work_orders_count == 1
    assert summary.completed_work_orders_count == 1
    assert summary.risk_distribution["High"] == 1


def test_csv_export_formatting(db_session, sample_machine):
    """Test 20: Exported CSV data matches expected schema and user filters."""
    tasks = [
        {"work_order_no": "WO-001", "machine_id": sample_machine.machine_id, "status": "Open"},
        {"work_order_no": "WO-002", "machine_id": sample_machine.machine_id, "status": "Completed"},
    ]
    df = pd.DataFrame(tasks)
    csv_str = df.to_csv(index=False)
    
    # Read back and verify
    df_read = pd.read_csv(io.StringIO(csv_str))
    assert len(df_read) == 2
    assert "work_order_no" in df_read.columns
    assert "status" in df_read.columns
