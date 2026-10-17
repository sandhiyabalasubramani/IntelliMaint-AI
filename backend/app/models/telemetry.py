"""
IntelliMaint AI — Telemetry Record SQLAlchemy Model
"""

from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(
        String(64),
        ForeignKey("machines.machine_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    air_temperature = Column(Float, nullable=False)
    process_temperature = Column(Float, nullable=False)
    rotational_speed = Column(Float, nullable=False)
    torque = Column(Float, nullable=False)
    tool_wear = Column(Float, nullable=False)
    machine_type_variant = Column(String(8), default="M", nullable=False)

    # Derived physics indicators
    temp_diff = Column(Float, nullable=True)
    mechanical_power = Column(Float, nullable=True)
    strain_product = Column(Float, nullable=True)

    # Inference tagging if ingested with model assessment
    failure_prediction = Column(Integer, nullable=True)
    failure_probability = Column(Float, nullable=True)
    risk_tier = Column(String(16), nullable=True)
    source_file = Column(String(128), nullable=True)

    # Relationship
    machine = relationship("Machine", back_populates="telemetry_records")
