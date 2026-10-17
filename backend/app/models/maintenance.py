"""
IntelliMaint AI — Maintenance Work Order SQLAlchemy Model
"""

from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    work_order_no = Column(String(64), unique=True, nullable=False, index=True)
    machine_id = Column(
        String(64),
        ForeignKey("machines.machine_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(
        String(32), default="Medium", nullable=False
    )  # Low, Medium, High, Critical
    technician = Column(String(128), nullable=True)
    due_date = Column(String(32), nullable=True)  # YYYY-MM-DD
    status = Column(
        String(32), default="Open", nullable=False
    )  # Open, In Progress, Completed, Cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    machine = relationship("Machine", back_populates="maintenance_tasks")
