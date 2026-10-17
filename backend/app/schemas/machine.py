"""
IntelliMaint AI — Machine Pydantic Schemas (Pydantic v2)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


OperationalStatus = Literal["OPERATIONAL", "DEGRADED", "MAINTENANCE", "OFFLINE"]


class MachineBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="Machine designation / name")
    machine_type: str = Field(..., min_length=2, max_length=64, description="Equipment category or type")
    department: Optional[str] = Field(None, max_length=128, description="Department or physical cell location")
    manufacturer: Optional[str] = Field(None, max_length=128, description="OEM equipment manufacturer")
    installation_date: Optional[str] = Field(None, description="Installation date in YYYY-MM-DD format")
    operational_status: OperationalStatus = Field(
        default="OPERATIONAL", description="Current operational state"
    )
    notes: Optional[str] = Field(None, max_length=2000, description="Engineering operational notes")


class MachineCreate(MachineBase):
    machine_id: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Unique alphanumeric machine identifier",
    )


class MachineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    machine_type: Optional[str] = Field(None, min_length=2, max_length=64)
    department: Optional[str] = Field(None, max_length=128)
    manufacturer: Optional[str] = Field(None, max_length=128)
    installation_date: Optional[str] = None
    operational_status: Optional[OperationalStatus] = None
    notes: Optional[str] = Field(None, max_length=2000)


class MachineResponse(MachineBase):
    id: int
    machine_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
