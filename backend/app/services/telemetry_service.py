"""
IntelliMaint AI — Telemetry Service & Validation Engine
"""

from __future__ import annotations
import io
import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from backend.app.models.telemetry import TelemetryRecord
from backend.app.models.machine import Machine
from backend.app.schemas.telemetry import TelemetryCreate, TelemetryIngestSummary
from ml.src.predictor import FailureRiskPredictor

# Column aliases to gracefully support canonical AI4I 2020 format or custom telemetry exports
COLUMN_MAPPINGS = {
    "air_temperature": ["Air temperature [K]", "air_temperature", "Air Temp", "air_temp"],
    "process_temperature": ["Process temperature [K]", "process_temperature", "Process Temp", "process_temp"],
    "rotational_speed": ["Rotational speed [rpm]", "rotational_speed", "RPM", "Speed [rpm]"],
    "torque": ["Torque [Nm]", "torque", "Torque", "torque_nm"],
    "tool_wear": ["Tool wear [min]", "tool_wear", "Tool Wear", "wear_min"],
    "machine_type_variant": ["Type", "machine_type_variant", "Quality Type", "Product Variant"],
    "machine_id": ["Machine Reference", "machine_id", "Product ID", "Machine ID", "UDI"],
}


class TelemetryValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class TelemetryService:
    @staticmethod
    def get_telemetry_records(
        db: Session,
        machine_id: Optional[str] = None,
        risk_tier: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TelemetryRecord]:
        query = db.query(TelemetryRecord)
        if machine_id:
            query = query.filter(TelemetryRecord.machine_id == machine_id)
        if risk_tier:
            query = query.filter(TelemetryRecord.risk_tier == risk_tier)
        return query.order_by(TelemetryRecord.timestamp.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def record_single_telemetry(db: Session, telem_in: TelemetryCreate) -> TelemetryRecord:
        # Check machine exists, or create fallback demo machine if not found
        machine = db.query(Machine).filter(Machine.machine_id == telem_in.machine_id).first()
        if not machine:
            machine = Machine(
                machine_id=telem_in.machine_id,
                name=f"Equipment {telem_in.machine_id}",
                machine_type="General Production Machine",
                operational_status="OPERATIONAL",
            )
            db.add(machine)
            db.commit()

        # Derive physics parameters
        temp_diff = round(telem_in.process_temperature - telem_in.air_temperature, 2)
        power = round((2.0 * np.pi * telem_in.rotational_speed / 60.0) * telem_in.torque, 2)
        strain = round(telem_in.torque * telem_in.tool_wear, 2)

        # Run predictor if ready
        predictor = FailureRiskPredictor()
        prob = None
        pred_class = None
        risk_tier = None

        if predictor.is_ready:
            try:
                res = predictor.predict_single({
                    "Air temperature [K]": telem_in.air_temperature,
                    "Process temperature [K]": telem_in.process_temperature,
                    "Rotational speed [rpm]": telem_in.rotational_speed,
                    "Torque [Nm]": telem_in.torque,
                    "Tool wear [min]": telem_in.tool_wear,
                    "Type": telem_in.machine_type_variant,
                })
                prob = res["failure_probability"]
                pred_class = res["predicted_failure"]
                risk_tier = res["risk_tier"]
            except Exception:
                pass

        record = TelemetryRecord(
            machine_id=telem_in.machine_id,
            air_temperature=telem_in.air_temperature,
            process_temperature=telem_in.process_temperature,
            rotational_speed=telem_in.rotational_speed,
            torque=telem_in.torque,
            tool_wear=telem_in.tool_wear,
            machine_type_variant=telem_in.machine_type_variant,
            temp_diff=temp_diff,
            mechanical_power=power,
            strain_product=strain,
            failure_prediction=pred_class,
            failure_probability=prob,
            risk_tier=risk_tier,
            source_file=telem_in.source_file or "direct_input",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def validate_and_parse_csv(
        file_bytes: bytes,
        filename: str = "uploaded_file.csv",
        max_size_mb: int = 15,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validates CSV file size, encoding, structural integrity, column presence,
        numeric formats, and range validity.
        """
        errors: List[str] = []

        # 1. Size check
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise TelemetryValidationException(
                f"File size ({size_mb:.2f} MB) exceeds maximum allowed size of {max_size_mb} MB."
            )

        if len(file_bytes) == 0:
            raise TelemetryValidationException("Uploaded CSV file is empty (0 bytes).")

        # 2. Decoding & Parsing
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_bytes.decode("latin-1")
            except Exception:
                raise TelemetryValidationException("Could not decode CSV file. Expected UTF-8 encoding.")

        try:
            df = pd.read_csv(io.StringIO(content))
        except Exception as e:
            raise TelemetryValidationException(f"Malformed CSV file structure: {str(e)}")

        if df.empty or len(df.columns) == 0:
            raise TelemetryValidationException("CSV contains no tabular data or columns.")

        # 3. Column mapping resolution
        resolved_cols: Dict[str, str] = {}
        for canonical, aliases in COLUMN_MAPPINGS.items():
            matched = None
            for alias in aliases:
                if alias in df.columns:
                    matched = alias
                    break
            if matched:
                resolved_cols[canonical] = matched

        # Mandatory canonical fields
        mandatory = ["air_temperature", "process_temperature", "rotational_speed", "torque", "tool_wear"]
        missing = [m for m in mandatory if m not in resolved_cols]
        if missing:
            raise TelemetryValidationException(
                f"Missing required telemetry columns: {missing}. "
                f"Expected standard headers such as 'Air temperature [K]', 'Process temperature [K]', "
                f"'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]'."
            )

        # 4. Standardize columns into a clean DataFrame
        clean_df = pd.DataFrame()
        for canonical in mandatory:
            clean_df[canonical] = pd.to_numeric(df[resolved_cols[canonical]], errors="coerce")

        # Categorical variant
        if "machine_type_variant" in resolved_cols:
            clean_df["machine_type_variant"] = df[resolved_cols["machine_type_variant"]].astype(str).str.strip().str.upper()
            clean_df["machine_type_variant"] = clean_df["machine_type_variant"].apply(
                lambda x: x if x in ["L", "M", "H"] else "M"
            )
        else:
            clean_df["machine_type_variant"] = "M"

        # Machine ID resolution
        if "machine_id" in resolved_cols:
            clean_df["machine_id"] = df[resolved_cols["machine_id"]].astype(str).str.strip()
        else:
            clean_df["machine_id"] = "CNC-MILL-01"  # Default correlation

        # 5. Row-level validation checks
        total_rows = len(clean_df)
        valid_indices = []

        for idx, row in clean_df.iterrows():
            row_errors = []
            # Check for NaN / infinite
            for col in mandatory:
                val = row[col]
                if pd.isna(val) or math.isinf(val):
                    row_errors.append(f"Row {idx + 1}: Column '{col}' is NaN or infinite.")

            if not row_errors:
                # Range verification
                if not (250.0 <= row["air_temperature"] <= 350.0):
                    row_errors.append(f"Row {idx + 1}: Air temp {row['air_temperature']} K outside plausible range (250-350 K).")
                if not (250.0 <= row["process_temperature"] <= 360.0):
                    row_errors.append(f"Row {idx + 1}: Process temp {row['process_temperature']} K outside plausible range (250-360 K).")
                if not (500.0 <= row["rotational_speed"] <= 5000.0):
                    row_errors.append(f"Row {idx + 1}: Speed {row['rotational_speed']} RPM outside plausible range (500-5000 RPM).")
                if not (0.0 <= row["torque"] <= 150.0):
                    row_errors.append(f"Row {idx + 1}: Torque {row['torque']} Nm outside plausible range (0-150 Nm).")
                if not (0.0 <= row["tool_wear"] <= 500.0):
                    row_errors.append(f"Row {idx + 1}: Tool wear {row['tool_wear']} min outside plausible range (0-500 min).")

            if row_errors:
                errors.extend(row_errors)
            else:
                valid_indices.append(idx)

        valid_df = clean_df.loc[valid_indices].copy()
        return valid_df, errors

    @staticmethod
    def ingest_validated_df(
        db: Session,
        valid_df: pd.DataFrame,
        filename: str = "batch_upload",
    ) -> TelemetryIngestSummary:
        """
        Enriches validated telemetry rows with ML predictions and stores them persistently.
        """
        if valid_df.empty:
            return TelemetryIngestSummary(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                high_risk_detected=0,
                medium_risk_detected=0,
                low_risk_detected=0,
                error_details=["No valid records to ingest."],
            )

        predictor = FailureRiskPredictor()

        # Map clean columns to ML predictor feature names
        ml_df = pd.DataFrame({
            "Air temperature [K]": valid_df["air_temperature"],
            "Process temperature [K]": valid_df["process_temperature"],
            "Rotational speed [rpm]": valid_df["rotational_speed"],
            "Torque [Nm]": valid_df["torque"],
            "Tool wear [min]": valid_df["tool_wear"],
            "Type": valid_df["machine_type_variant"],
        })

        if predictor.is_ready:
            pred_results = predictor.predict_batch(ml_df)
            valid_df["failure_probability"] = pred_results["failure_probability"]
            valid_df["predicted_failure"] = pred_results["predicted_failure"]
            valid_df["risk_tier"] = pred_results["risk_tier"]
            valid_df["temp_diff"] = pred_results["temp_diff_kelvin"]
            valid_df["mechanical_power"] = pred_results["mechanical_power_watts"]
            valid_df["strain_product"] = pred_results["strain_product"]
        else:
            valid_df["failure_probability"] = 0.05
            valid_df["predicted_failure"] = 0
            valid_df["risk_tier"] = "Low"
            valid_df["temp_diff"] = np.round(valid_df["process_temperature"] - valid_df["air_temperature"], 2)
            valid_df["mechanical_power"] = np.round((2.0 * np.pi * valid_df["rotational_speed"] / 60.0) * valid_df["torque"], 2)
            valid_df["strain_product"] = np.round(valid_df["torque"] * valid_df["tool_wear"], 2)

        # Verify or register machines
        unique_machines = valid_df["machine_id"].unique()
        for m_id in unique_machines:
            m = db.query(Machine).filter(Machine.machine_id == m_id).first()
            if not m:
                m = Machine(
                    machine_id=m_id,
                    name=f"Machine {m_id}",
                    machine_type="CNC Milling Machine",
                    operational_status="OPERATIONAL",
                )
                db.add(m)
        db.commit()

        # Bulk insert telemetry records
        records_to_add = []
        for _, row in valid_df.iterrows():
            rec = TelemetryRecord(
                machine_id=row["machine_id"],
                air_temperature=float(row["air_temperature"]),
                process_temperature=float(row["process_temperature"]),
                rotational_speed=float(row["rotational_speed"]),
                torque=float(row["torque"]),
                tool_wear=float(row["tool_wear"]),
                machine_type_variant=row["machine_type_variant"],
                temp_diff=float(row["temp_diff"]),
                mechanical_power=float(row["mechanical_power"]),
                strain_product=float(row["strain_product"]),
                failure_prediction=int(row["predicted_failure"]),
                failure_probability=float(row["failure_probability"]),
                risk_tier=row["risk_tier"],
                source_file=filename,
            )
            records_to_add.append(rec)

        db.bulk_save_objects(records_to_add)
        db.commit()

        high_count = int((valid_df["risk_tier"] == "High").sum())
        med_count = int((valid_df["risk_tier"] == "Medium").sum())
        low_count = int((valid_df["risk_tier"] == "Low").sum())

        return TelemetryIngestSummary(
            total_records=len(valid_df),
            valid_records=len(valid_df),
            invalid_records=0,
            high_risk_detected=high_count,
            medium_risk_detected=med_count,
            low_risk_detected=low_count,
        )
