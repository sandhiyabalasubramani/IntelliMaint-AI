"""
IntelliMaint AI — Health Check Router
"""

from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db
from backend.app.config import settings
from ml.src.predictor import FailureRiskPredictor

router = APIRouter(tags=["System Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive system health check:
    - Application status
    - Database engine & connectivity ping
    - ML model artifact readiness
    """
    # 1. Check Database
    db_status = "unhealthy"
    db_engine = settings.DATABASE_URL.split(":")[0]
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"database error: {str(e)}"

    # 2. Check ML Predictor
    predictor = FailureRiskPredictor()
    ml_status = "ready" if predictor.is_ready else "not_trained"
    meta = predictor.get_metadata()

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": {
            "engine": db_engine,
            "status": db_status,
        },
        "machine_learning": {
            "status": ml_status,
            "model_version": meta.get("model_version"),
            "champion_algorithm": meta.get("champion_algorithm"),
        },
    }
