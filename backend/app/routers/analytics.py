"""
IntelliMaint AI — Fleet Analytics & KPI Router
"""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.analytics import FleetSummaryResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Fleet Analytics"])


@router.get("/summary", response_model=FleetSummaryResponse)
def get_fleet_summary(db: Session = Depends(get_db)):
    """
    Retrieve real, database-derived fleet health KPIs:
    - Total registered machines
    - Current risk breakdown (High, Medium, Low)
    - Work order operational backlog
    - Machine-level risk overview
    """
    return AnalyticsService.get_fleet_summary(db)
