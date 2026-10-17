"""
IntelliMaint AI — Schemas Package
"""

from backend.app.schemas.machine import (
    MachineBase,
    MachineCreate,
    MachineUpdate,
    MachineResponse,
)
from backend.app.schemas.telemetry import (
    TelemetryBase,
    TelemetryCreate,
    TelemetryResponse,
    TelemetryIngestSummary,
)
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)
from backend.app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    VALID_STATUS_TRANSITIONS,
)
from backend.app.schemas.analytics import (
    FleetSummaryResponse,
    MachineRiskItem,
)

__all__ = [
    "MachineBase",
    "MachineCreate",
    "MachineUpdate",
    "MachineResponse",
    "TelemetryBase",
    "TelemetryCreate",
    "TelemetryResponse",
    "TelemetryIngestSummary",
    "PredictionRequest",
    "PredictionResponse",
    "MaintenanceCreate",
    "MaintenanceUpdate",
    "MaintenanceResponse",
    "VALID_STATUS_TRANSITIONS",
    "FleetSummaryResponse",
    "MachineRiskItem",
]
