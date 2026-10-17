"""
IntelliMaint AI — Prediction Pydantic Schemas (Pydantic v2)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class PredictionRequest(BaseModel):
    machine_id: str = Field(..., min_length=2, max_length=64, description="Target machine ID")
    air_temperature: float = Field(..., ge=250.0, le=350.0, description="Ambient air temperature in Kelvin")
    process_temperature: float = Field(..., ge=250.0, le=360.0, description="Process temperature in Kelvin")
    rotational_speed: float = Field(..., ge=500.0, le=5000.0, description="Spindle speed in RPM")
    torque: float = Field(..., ge=0.0, le=150.0, description="Torque in Nm")
    tool_wear: float = Field(..., ge=0.0, le=500.0, description="Tool wear time in minutes")
    machine_type_variant: Literal["L", "M", "H"] = Field(default="M", description="Tool quality grade")


class PredictionResponse(BaseModel):
    prediction_id: str
    machine_id: str
    timestamp: datetime
    failure_probability: float
    predicted_failure: int
    risk_category: str
    model_version: str
    model_algorithm: str
    physical_indicators: Optional[Dict[str, float]] = None
    contributing_factors: List[Dict[str, Any]] = []
    suggested_actions: List[str] = []
    disclaimer: str

    model_config = ConfigDict(from_attributes=True)
