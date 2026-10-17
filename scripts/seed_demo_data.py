"""
IntelliMaint AI — Idempotent Demonstration Data Seeder

Seeds realistic demonstration machines, telemetry records,
model predictions, and maintenance work orders. Can be run repeatedly
without creating duplicate records.
"""

from __future__ import annotations
import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import SessionLocal, init_db
from backend.app.models.machine import Machine
from backend.app.models.telemetry import TelemetryRecord
from backend.app.models.prediction import PredictionRecord
from backend.app.models.maintenance import MaintenanceTask
from ml.src.predictor import FailureRiskPredictor


DEMO_MACHINES = [
    {
        "machine_id": "CNC-MILL-01",
        "name": "5-Axis High-Speed CNC Machining Center",
        "machine_type": "CNC Milling Machine",
        "department": "Machining Cell Alpha",
        "manufacturer": "DMG MORI",
        "installation_date": "2023-03-15",
        "operational_status": "OPERATIONAL",
        "notes": "Dedicated to titanium aerospace impeller milling. Regular spindle lubrication required.",
    },
    {
        "machine_id": "CNC-MILL-02",
        "name": "Heavy Duty Vertical Machining Center",
        "machine_type": "CNC Milling Machine",
        "department": "Machining Cell Beta",
        "manufacturer": "Haas Automation",
        "installation_date": "2022-08-10",
        "operational_status": "DEGRADED",
        "notes": "Showing elevated tool wear and micro-vibration in high-torque roughing operations.",
    },
    {
        "machine_id": "LATHE-TUR-01",
        "name": "Twin-Spindle Precision CNC Lathe",
        "machine_type": "CNC Turning Center",
        "department": "Precision Turning Bay",
        "manufacturer": "Mazak Corporation",
        "installation_date": "2023-11-01",
        "operational_status": "OPERATIONAL",
        "notes": "High-precision shaft manufacturing with automated bar feeder.",
    },
    {
        "machine_id": "HYDR-PUMP-01",
        "name": "High-Pressure Hydraulic Power Unit (350 Bar)",
        "machine_type": "Hydraulic Power System",
        "department": "Stamping & Press Facility",
        "manufacturer": "Bosch Rexroth",
        "installation_date": "2021-05-20",
        "operational_status": "MAINTENANCE",
        "notes": "Undergoing scheduled filter cartridge replacement and seal inspection.",
    },
    {
        "machine_id": "ROBO-WELD-01",
        "name": "6-Axis Robotic Arc Welding Cell",
        "machine_type": "Industrial Robot",
        "department": "Automated Fabrication Line",
        "manufacturer": "FANUC Robotics",
        "installation_date": "2024-01-18",
        "operational_status": "OPERATIONAL",
        "notes": "Equipped with water-cooled torch and seam-tracking laser optical sensor.",
    },
    {
        "machine_id": "COMP-AIR-01",
        "name": "Variable Speed Rotary Screw Air Compressor",
        "machine_type": "Pneumatics & Air System",
        "department": "Central Utility Plant",
        "manufacturer": "Atlas Copco",
        "installation_date": "2020-09-12",
        "operational_status": "OPERATIONAL",
        "notes": "Supplies shop air at 7.5 bar across the entire plant.",
    },
]


DEMO_TELEMETRY = [
    # Normal operation
    {
        "machine_id": "CNC-MILL-01",
        "air_temperature": 298.2,
        "process_temperature": 308.5,
        "rotational_speed": 1520.0,
        "torque": 39.5,
        "tool_wear": 42.0,
        "machine_type_variant": "M",
    },
    # High tool wear & elevated torque (At-Risk)
    {
        "machine_id": "CNC-MILL-02",
        "air_temperature": 301.8,
        "process_temperature": 310.2,
        "rotational_speed": 1350.0,
        "torque": 62.4,
        "tool_wear": 218.0,
        "machine_type_variant": "L",
    },
    # Normal operation
    {
        "machine_id": "LATHE-TUR-01",
        "air_temperature": 299.4,
        "process_temperature": 309.1,
        "rotational_speed": 1640.0,
        "torque": 34.2,
        "tool_wear": 65.0,
        "machine_type_variant": "H",
    },
    # Thermal Dissipation anomaly
    {
        "machine_id": "HYDR-PUMP-01",
        "air_temperature": 302.5,
        "process_temperature": 308.2,  # Delta T is only 5.7 K
        "rotational_speed": 1320.0,
        "torque": 55.0,
        "tool_wear": 95.0,
        "machine_type_variant": "M",
    },
    # Normal operation
    {
        "machine_id": "ROBO-WELD-01",
        "air_temperature": 297.8,
        "process_temperature": 307.2,
        "rotational_speed": 1490.0,
        "torque": 41.0,
        "tool_wear": 25.0,
        "machine_type_variant": "M",
    },
    # Normal operation
    {
        "machine_id": "COMP-AIR-01",
        "air_temperature": 296.5,
        "process_temperature": 306.4,
        "rotational_speed": 1580.0,
        "torque": 36.8,
        "tool_wear": 110.0,
        "machine_type_variant": "L",
    },
]


DEMO_WORK_ORDERS = [
    {
        "work_order_no": "WO-2026-001",
        "machine_id": "CNC-MILL-02",
        "title": "Urgent Spindle Cutting Insert Replacement",
        "description": "Telemetry indicated critical tool wear (>200 min) with elevated cutting torque. Replace carbide inserts and verify runout.",
        "priority": "High",
        "technician": "Marcus Vance (Senior Machinist)",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d"),
        "status": "In Progress",
        "notes": "Replacement Sandvik Coromant inserts requisitioned from tool crib.",
    },
    {
        "work_order_no": "WO-2026-002",
        "machine_id": "HYDR-PUMP-01",
        "title": "Hydraulic Cooler Heat Exchanger De-scaling",
        "description": "Temperature delta dropped below 8.0 K indicating thermal dissipation degradation. Clean radiator fins and flush coolant lines.",
        "priority": "Critical",
        "technician": "Elena Rostova (Fluid Power Specialist)",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d"),
        "status": "Open",
        "notes": "System isolated and tagged out for coolant circuit service.",
    },
    {
        "work_order_no": "WO-2026-003",
        "machine_id": "CNC-MILL-01",
        "title": "Quarterly 5-Axis Ballbar Calibration & Axis Lube",
        "description": "Regular ISO 230-4 circularity test and automated central lubrication reservoir refill.",
        "priority": "Medium",
        "technician": "David Chen (Maintenance Tech)",
        "due_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
        "status": "Completed",
        "notes": "Ballbar circular deviation measured 4.2 micrometers (within manufacturer tolerance 5.0). Completed successfully.",
    },
    {
        "work_order_no": "WO-2026-004",
        "machine_id": "COMP-AIR-01",
        "title": "Air Intake Pre-Filter Replacement",
        "description": "Scheduled monthly intake filter inspection and moisture trap drain check.",
        "priority": "Low",
        "technician": "Priya Patel (Facility Operations)",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        "status": "Open",
        "notes": "Standard maintenance kit in inventory.",
    },
]


def seed_database(verbose: bool = True) -> None:
    init_db()
    db = SessionLocal()
    predictor = FailureRiskPredictor()

    if verbose:
        print("=" * 60)
        print("IntelliMaint AI — Demonstration Data Seeding")
        print("=" * 60)

    try:
        # 1. Seed Machines
        seeded_machines = 0
        for m_data in DEMO_MACHINES:
            existing = db.query(Machine).filter(Machine.machine_id == m_data["machine_id"]).first()
            if not existing:
                machine = Machine(**m_data)
                db.add(machine)
                seeded_machines += 1
            else:
                # Update attributes
                for k, v in m_data.items():
                    setattr(existing, k, v)
        db.commit()
        if verbose:
            print(f" -> Machines: {seeded_machines} added, {len(DEMO_MACHINES) - seeded_machines} updated.")

        # 2. Seed Telemetry & Predictions
        seeded_telemetry = 0
        seeded_predictions = 0

        for telem in DEMO_TELEMETRY:
            m_id = telem["machine_id"]
            # Derive indicators
            speed = telem["rotational_speed"]
            torque = telem["torque"]
            wear = telem["tool_wear"]
            air_t = telem["air_temperature"]
            proc_t = telem["process_temperature"]
            temp_diff = round(proc_t - air_t, 2)
            power = round((2.0 * 3.1415926535 * speed / 60.0) * torque, 2)
            strain = round(torque * wear, 2)

            # Predict if predictor ready
            pred_class = 0
            prob = 0.05
            risk_tier = "Low"
            factors = []
            actions = ["Telemetry within nominal boundaries."]
            model_ver = "1.0.0"
            algorithm = "Demonstration"

            if predictor.is_ready:
                try:
                    res = predictor.predict_single({
                        "Air temperature [K]": air_t,
                        "Process temperature [K]": proc_t,
                        "Rotational speed [rpm]": speed,
                        "Torque [Nm]": torque,
                        "Tool wear [min]": wear,
                        "Type": telem.get("machine_type_variant", "M"),
                    })
                    prob = res["failure_probability"]
                    pred_class = res["predicted_failure"]
                    risk_tier = res["risk_tier"]
                    factors = res["contributing_factors"]
                    actions = res["suggested_actions"]
                    model_ver = res["model_version"]
                    algorithm = res["model_algorithm"]
                except Exception as e:
                    if verbose:
                        print(f"Prediction fallback for {m_id}: {e}")

            # Create telemetry record if none exists for this machine
            existing_telem = db.query(TelemetryRecord).filter(TelemetryRecord.machine_id == m_id).first()
            if not existing_telem:
                record = TelemetryRecord(
                    machine_id=m_id,
                    air_temperature=air_t,
                    process_temperature=proc_t,
                    rotational_speed=speed,
                    torque=torque,
                    tool_wear=wear,
                    machine_type_variant=telem.get("machine_type_variant", "M"),
                    temp_diff=temp_diff,
                    mechanical_power=power,
                    strain_product=strain,
                    failure_prediction=pred_class,
                    failure_probability=prob,
                    risk_tier=risk_tier,
                    source_file="demo_seed",
                )
                db.add(record)
                seeded_telemetry += 1

            # Create prediction record if none exists
            existing_pred = db.query(PredictionRecord).filter(PredictionRecord.machine_id == m_id).first()
            if not existing_pred:
                pred_record = PredictionRecord(
                    prediction_id=f"PRED-{uuid.uuid4().hex[:8].upper()}",
                    machine_id=m_id,
                    failure_probability=prob,
                    predicted_failure=pred_class,
                    risk_category=risk_tier,
                    model_version=model_ver,
                    model_algorithm=algorithm,
                    contributing_factors=json.dumps(factors),
                    suggested_actions=json.dumps(actions),
                    input_telemetry=json.dumps(telem),
                )
                db.add(pred_record)
                seeded_predictions += 1

        db.commit()
        if verbose:
            print(f" -> Telemetry records seeded: {seeded_telemetry}")
            print(f" -> Model prediction records seeded: {seeded_predictions}")

        # 3. Seed Maintenance Work Orders
        seeded_wo = 0
        for wo in DEMO_WORK_ORDERS:
            existing_wo = db.query(MaintenanceTask).filter(MaintenanceTask.work_order_no == wo["work_order_no"]).first()
            if not existing_wo:
                task = MaintenanceTask(
                    work_order_no=wo["work_order_no"],
                    machine_id=wo["machine_id"],
                    title=wo["title"],
                    description=wo["description"],
                    priority=wo["priority"],
                    technician=wo["technician"],
                    due_date=wo["due_date"],
                    status=wo["status"],
                    notes=wo["notes"],
                    completed_at=datetime.now(timezone.utc) if wo["status"] == "Completed" else None,
                )
                db.add(task)
                seeded_wo += 1
            else:
                for k, v in wo.items():
                    setattr(existing_wo, k, v)
        db.commit()
        if verbose:
            print(f" -> Maintenance Work Orders: {seeded_wo} added, {len(DEMO_WORK_ORDERS) - seeded_wo} updated.")
            print("\nDatabase seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during database seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
