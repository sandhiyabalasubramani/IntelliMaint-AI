"""
IntelliMaint AI — Prediction Service
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.prediction import PredictionRecord
from backend.app.models.machine import Machine
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from ml.src.predictor import FailureRiskPredictor, ModelNotTrainedError


class PredictionService:
    @staticmethod
    def get_predictions(
        db: Session,
        machine_id: Optional[str] = None,
        risk_category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PredictionRecord]:
        query = db.query(PredictionRecord)
        if machine_id:
            query = query.filter(PredictionRecord.machine_id == machine_id)
        if risk_category:
            query = query.filter(PredictionRecord.risk_category == risk_category)
        return query.order_by(PredictionRecord.timestamp.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_prediction_by_id(db: Session, prediction_id: str) -> Optional[PredictionRecord]:
        return db.query(PredictionRecord).filter(PredictionRecord.prediction_id == prediction_id).first()

    @staticmethod
    def create_prediction(db: Session, req: PredictionRequest) -> PredictionResponse:
        # Check machine exists or create fallback demo machine
        machine = db.query(Machine).filter(Machine.machine_id == req.machine_id).first()
        if not machine:
            machine = Machine(
                machine_id=req.machine_id,
                name=f"Machine {req.machine_id}",
                machine_type="CNC Milling Machine",
                operational_status="OPERATIONAL",
            )
            db.add(machine)
            db.commit()

        predictor = FailureRiskPredictor()
        if not predictor.is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Machine learning model is not yet trained. Run training via ml/src/train.py or scripts/train_model.py.",
            )

        telemetry_dict = {
            "Air temperature [K]": req.air_temperature,
            "Process temperature [K]": req.process_temperature,
            "Rotational speed [rpm]": req.rotational_speed,
            "Torque [Nm]": req.torque,
            "Tool wear [min]": req.tool_wear,
            "Type": req.machine_type_variant,
        }

        pred_res = predictor.predict_single(telemetry_dict)

        pred_id = f"PRED-{uuid.uuid4().hex[:8].upper()}"

        record = PredictionRecord(
            prediction_id=pred_id,
            machine_id=req.machine_id,
            timestamp=datetime.now(timezone.utc),
            failure_probability=pred_res["failure_probability"],
            predicted_failure=pred_res["predicted_failure"],
            risk_category=pred_res["risk_tier"],
            model_version=pred_res["model_version"],
            model_algorithm=pred_res["model_algorithm"],
            contributing_factors=json.dumps(pred_res["contributing_factors"]),
            suggested_actions=json.dumps(pred_res["suggested_actions"]),
            input_telemetry=json.dumps(telemetry_dict),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return PredictionResponse(
            prediction_id=record.prediction_id,
            machine_id=record.machine_id,
            timestamp=record.timestamp,
            failure_probability=record.failure_probability,
            predicted_failure=record.predicted_failure,
            risk_category=record.risk_category,
            model_version=record.model_version,
            model_algorithm=record.model_algorithm,
            physical_indicators=pred_res["physical_indicators"],
            contributing_factors=pred_res["contributing_factors"],
            suggested_actions=pred_res["suggested_actions"],
            disclaimer=pred_res["disclaimer"],
        )
