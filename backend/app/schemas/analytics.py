"""
IntelliMaint AI — Analytics & Fleet Summary Schemas (Pydantic v2)
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class MachineRiskItem(BaseModel):
    machine_id: str
    name: str
    machine_type: str
    department: Optional[str] = None
    operational_status: str
    latest_failure_prob: float
    latest_risk_tier: str
    latest_prediction_id: Optional[str] = None
    open_work_orders_count: int


class FleetSummaryResponse(BaseModel):
    total_registered_machines: int
    high_risk_machines_count: int
    medium_risk_machines_count: int
    low_risk_machines_count: int
    open_work_orders_count: int
    completed_work_orders_count: int
    latest_telemetry_timestamp: Optional[str] = None
    risk_distribution: Dict[str, int]
    machine_type_distribution: Dict[str, int]
    operational_status_distribution: Dict[str, int]
    machine_risk_overview: List[MachineRiskItem]
