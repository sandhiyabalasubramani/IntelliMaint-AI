"""
IntelliMaint AI — Telemetry Pydantic Schemas (Pydantic v2)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


MachineTypeVariant = Literal["L", "M", "H"]


class TelemetryBase(BaseModel):
    air_temperature: float = Field(
        ...,
        ge=250.0,
        le=350.0,
        description="Ambient air temperature in Kelvin (nominal ~295K - 305K)",
    )
    process_temperature: float = Field(
        ...,
        ge=250.0,
        le=360.0,
        description="Cutting zone / process temperature in Kelvin (nominal ~305K - 315K)",
    )
    rotational_speed: float = Field(
        ...,
        ge=500.0,
        le=5000.0,
        description="Spindle rotational speed in RPM (nominal ~1200 - 2800 RPM)",
    )
    torque: float = Field(
        ...,
        ge=0.0,
        le=150.0,
        description="Cutting torque in Newton-meters (nominal ~10 - 80 Nm)",
    )
    tool_wear: float = Field(
        ...,
        ge=0.0,
        le=500.0,
        description="Cumulative tool wear time in minutes (nominal 0 - 250 min)",
    )
    machine_type_variant: MachineTypeVariant = Field(
        default="M",
        description="Product / tooling quality grade: L (Low), M (Medium), H (High)",
    )

    @field_validator("process_temperature")
    @classmethod
    def validate_thermal_physics(cls, v: float, info) -> float:
        air = info.data.get("air_temperature")
        if air is not None and v < (air - 5.0):
            # Physical process temperature should not be significantly lower than ambient air in operating machinery
            raise ValueError("Process temperature cannot be more than 5 K below ambient air temperature.")
        return v


class TelemetryCreate(TelemetryBase):
    machine_id: str = Field(..., min_length=2, max_length=64)
    source_file: Optional[str] = Field(default=None, max_length=128)


class TelemetryResponse(TelemetryBase):
    id: int
    machine_id: str
    timestamp: datetime
    temp_diff: Optional[float] = None
    mechanical_power: Optional[float] = None
    strain_product: Optional[float] = None
    failure_prediction: Optional[int] = None
    failure_probability: Optional[float] = None
    risk_tier: Optional[str] = None
    source_file: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TelemetryIngestSummary(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    high_risk_detected: int
    medium_risk_detected: int
    low_risk_detected: int
    error_details: List[str] = []
