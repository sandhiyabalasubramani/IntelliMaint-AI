"""
IntelliMaint AI — Machine Risk Predictions Router
"""

from __future__ import annotations
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)
from backend.app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Risk Predictions"])


@router.get("", response_model=List[PredictionResponse])
def get_predictions(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category (Low, Medium, High)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve historical prediction records with contributing factors."""
    records = PredictionService.get_predictions(
        db, machine_id=machine_id, risk_category=risk_category, skip=skip, limit=limit
    )

    results = []
    for r in records:
        factors = json.loads(r.contributing_factors) if r.contributing_factors else []
        actions = json.loads(r.suggested_actions) if r.suggested_actions else []
        results.append(
            PredictionResponse(
                prediction_id=r.prediction_id,
                machine_id=r.machine_id,
                timestamp=r.timestamp,
                failure_probability=r.failure_probability,
                predicted_failure=r.predicted_failure,
                risk_category=r.risk_category,
                model_version=r.model_version,
                model_algorithm=r.model_algorithm,
                contributing_factors=factors,
                suggested_actions=actions,
                disclaimer=(
                    "Educational and portfolio demonstration. Risk categories are operational indicators, "
                    "not certified industrial safety thresholds."
                ),
            )
        )
    return results


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
    prediction_in: PredictionRequest,
    db: Session = Depends(get_db),
):
    """Run real-time ML risk assessment and record predictions with explainability factors."""
    return PredictionService.create_prediction(db, prediction_in)


@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction_by_id(
    prediction_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a single historical prediction assessment by ID."""
    r = PredictionService.get_prediction_by_id(db, prediction_id)
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction record '{prediction_id}' not found.",
        )

    factors = json.loads(r.contributing_factors) if r.contributing_factors else []
    actions = json.loads(r.suggested_actions) if r.suggested_actions else []

    return PredictionResponse(
        prediction_id=r.prediction_id,
        machine_id=r.machine_id,
        timestamp=r.timestamp,
        failure_probability=r.failure_probability,
        predicted_failure=r.predicted_failure,
        risk_category=r.risk_category,
        model_version=r.model_version,
        model_algorithm=r.model_algorithm,
        contributing_factors=factors,
        suggested_actions=actions,
        disclaimer=(
            "Educational and portfolio demonstration. Risk categories are operational indicators, "
            "not certified industrial safety thresholds."
        ),
    )
