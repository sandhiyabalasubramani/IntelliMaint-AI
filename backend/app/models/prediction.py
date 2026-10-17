"""
IntelliMaint AI — Prediction Record SQLAlchemy Model
"""

from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prediction_id = Column(String(64), unique=True, nullable=False, index=True)
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
    failure_probability = Column(Float, nullable=False)
    predicted_failure = Column(Integer, nullable=False)
    risk_category = Column(String(16), nullable=False)  # Low, Medium, High
    model_version = Column(String(32), nullable=False)
    model_algorithm = Column(String(64), nullable=False)

    # Serialized JSON structures
    contributing_factors = Column(Text, nullable=True)
    suggested_actions = Column(Text, nullable=True)
    input_telemetry = Column(Text, nullable=True)

    # Relationship
    machine = relationship("Machine", back_populates="predictions")
