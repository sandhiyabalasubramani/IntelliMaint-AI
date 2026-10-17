"""
IntelliMaint AI — Maintenance Task Pydantic Schemas (Pydantic v2)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


WorkOrderPriority = Literal["Low", "Medium", "High", "Critical"]
WorkOrderStatus = Literal["Open", "In Progress", "Completed", "Cancelled"]


VALID_STATUS_TRANSITIONS = {
    "Open": ["Open", "In Progress", "Cancelled"],
    "In Progress": ["In Progress", "Completed", "Cancelled", "Open"],
    "Completed": ["Completed", "In Progress"],  # Can re-open to In Progress
    "Cancelled": ["Cancelled", "Open"],          # Can re-open to Open
}


class MaintenanceCreate(BaseModel):
    machine_id: str = Field(..., min_length=2, max_length=64, description="Target machine ID")
    title: str = Field(..., min_length=3, max_length=255, description="Work order title")
    description: Optional[str] = Field(None, description="Detailed problem description or scope")
    priority: WorkOrderPriority = Field(default="Medium", description="Maintenance urgency priority")
    technician: Optional[str] = Field(None, max_length=128, description="Assigned technician or engineering team")
    due_date: Optional[str] = Field(None, description="Target due date in YYYY-MM-DD")
    status: WorkOrderStatus = Field(default="Open", description="Initial work order status")
    notes: Optional[str] = Field(None, description="Initial resolution notes")


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    priority: Optional[WorkOrderPriority] = None
    technician: Optional[str] = Field(None, max_length=128)
    due_date: Optional[str] = None
    status: Optional[WorkOrderStatus] = None
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    work_order_no: str
    machine_id: str
    title: str
    description: Optional[str] = None
    priority: str
    technician: Optional[str] = None
    due_date: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
