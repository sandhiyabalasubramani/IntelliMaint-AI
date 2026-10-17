"""
IntelliMaint AI — Analytics & Fleet Aggregation Service
"""

from __future__ import annotations
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.machine import Machine
from backend.app.models.telemetry import TelemetryRecord
from backend.app.models.prediction import PredictionRecord
from backend.app.models.maintenance import MaintenanceTask
from backend.app.schemas.analytics import FleetSummaryResponse, MachineRiskItem


class AnalyticsService:
    @staticmethod
    def get_fleet_summary(db: Session) -> FleetSummaryResponse:
        # Total registered machines
        machines = db.query(Machine).all()
        total_machines = len(machines)

        # Work orders counts
        open_wo_count = (
            db.query(MaintenanceTask)
            .filter(MaintenanceTask.status.in_(["Open", "In Progress"]))
            .count()
        )
        completed_wo_count = (
            db.query(MaintenanceTask)
            .filter(MaintenanceTask.status == "Completed")
            .count()
        )

        # Latest telemetry timestamp
        latest_telem = (
            db.query(TelemetryRecord.timestamp)
            .order_by(TelemetryRecord.timestamp.desc())
            .first()
        )
        latest_telem_ts = latest_telem[0].isoformat() if latest_telem else None

        # Machine-level risk overview
        machine_overview: List[MachineRiskItem] = []
        risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
        machine_type_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for m in machines:
            # Type and status counts
            machine_type_counts[m.machine_type] = machine_type_counts.get(m.machine_type, 0) + 1
            status_counts[m.operational_status] = status_counts.get(m.operational_status, 0) + 1

            # Get latest prediction for this machine
            latest_pred = (
                db.query(PredictionRecord)
                .filter(PredictionRecord.machine_id == m.machine_id)
                .order_by(PredictionRecord.timestamp.desc())
                .first()
            )

            # Get open work order count for this machine
            m_open_wo = (
                db.query(MaintenanceTask)
                .filter(
                    MaintenanceTask.machine_id == m.machine_id,
                    MaintenanceTask.status.in_(["Open", "In Progress"]),
                )
                .count()
            )

            if latest_pred:
                prob = latest_pred.failure_probability
                tier = latest_pred.risk_category
                pred_id = latest_pred.prediction_id
                risk_counts[tier] = risk_counts.get(tier, 0) + 1
            else:
                # Fallback to latest telemetry if available
                latest_tel = (
                    db.query(TelemetryRecord)
                    .filter(TelemetryRecord.machine_id == m.machine_id)
                    .order_by(TelemetryRecord.timestamp.desc())
                    .first()
                )
                if latest_tel and latest_tel.failure_probability is not None:
                    prob = latest_tel.failure_probability
                    tier = latest_tel.risk_tier or "Low"
                    pred_id = None
                    risk_counts[tier] = risk_counts.get(tier, 0) + 1
                else:
                    prob = 0.0
                    tier = "Low"
                    pred_id = None
                    risk_counts["Low"] += 1

            machine_overview.append(
                MachineRiskItem(
                    machine_id=m.machine_id,
                    name=m.name,
                    machine_type=m.machine_type,
                    department=m.department,
                    operational_status=m.operational_status,
                    latest_failure_prob=prob,
                    latest_risk_tier=tier,
                    latest_prediction_id=pred_id,
                    open_work_orders_count=m_open_wo,
                )
            )

        return FleetSummaryResponse(
            total_registered_machines=total_machines,
            high_risk_machines_count=risk_counts["High"],
            medium_risk_machines_count=risk_counts["Medium"],
            low_risk_machines_count=risk_counts["Low"],
            open_work_orders_count=open_wo_count,
            completed_work_orders_count=completed_wo_count,
            latest_telemetry_timestamp=latest_telem_ts,
            risk_distribution={
                "High": risk_counts["High"],
                "Medium": risk_counts["Medium"],
                "Low": risk_counts["Low"],
            },
            machine_type_distribution=machine_type_counts,
            operational_status_distribution=status_counts,
            machine_risk_overview=machine_overview,
        )
