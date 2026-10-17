"""
IntelliMaint AI — Telemetry Ingestion Router
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.telemetry import (
    TelemetryCreate,
    TelemetryResponse,
    TelemetryIngestSummary,
)
from backend.app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingestion"])


@router.get("", response_model=List[TelemetryResponse])
def get_telemetry(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    risk_tier: Optional[str] = Query(None, description="Filter by risk tier (Low, Medium, High)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Query telemetry records with optional machine and risk tier filters."""
    return TelemetryService.get_telemetry_records(
        db, machine_id=machine_id, risk_tier=risk_tier, skip=skip, limit=limit
    )


@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
def record_telemetry(
    telemetry_in: TelemetryCreate,
    db: Session = Depends(get_db),
):
    """Record a single telemetry reading with automatic physics & risk evaluation."""
    return TelemetryService.record_single_telemetry(db, telemetry_in)


@router.post("/upload", response_model=TelemetryIngestSummary, status_code=status.HTTP_200_OK)
async def upload_telemetry_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest telemetry CSV file.
    Validates headers, numerical formats, and ranges, then evaluates failure risk and stores records.
    """
    file_bytes = await file.read()
    valid_df, errors = TelemetryService.validate_and_parse_csv(
        file_bytes, filename=file.filename or "upload.csv"
    )

    summary = TelemetryService.ingest_validated_df(
        db, valid_df=valid_df, filename=file.filename or "upload.csv"
    )
    summary.error_details = errors[:10]  # Return top 10 validation notes if any
    return summary
