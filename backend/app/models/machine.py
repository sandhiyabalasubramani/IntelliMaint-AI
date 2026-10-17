"""
IntelliMaint AI — Machine SQLAlchemy Model
"""

from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    machine_type = Column(String(64), nullable=False)  # e.g. CNC Milling Machine, Lathe, Industrial Pump
    department = Column(String(128), nullable=True)  # e.g. Machining Cell A, Assembly Bay 2
    manufacturer = Column(String(128), nullable=True)  # e.g. DMG MORI, Haas Automation
    installation_date = Column(String(32), nullable=True)  # YYYY-MM-DD
    operational_status = Column(
        String(32), default="OPERATIONAL", nullable=False
    )  # OPERATIONAL, DEGRADED, MAINTENANCE, OFFLINE
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

    # Relationships
    telemetry_records = relationship(
        "TelemetryRecord",
        back_populates="machine",
        cascade="all, delete-orphan",
    )
    predictions = relationship(
        "PredictionRecord",
        back_populates="machine",
        cascade="all, delete-orphan",
    )
    maintenance_tasks = relationship(
        "MaintenanceTask",
        back_populates="machine",
        cascade="all, delete-orphan",
    )
