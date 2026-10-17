"""
IntelliMaint AI — Telemetry Data Ingestion & Validation Tests
"""

import pytest
import pandas as pd
from backend.app.services.telemetry_service import (
    TelemetryService,
    TelemetryValidationException,
)
from ml.src.dataset import generate_synthetic_telemetry, CANONICAL_COLUMNS


def test_empty_csv_raises_exception():
    """Test 6: Ingesting an empty CSV file raises a descriptive validation exception."""
    empty_bytes = b""
    with pytest.raises(TelemetryValidationException) as exc:
        TelemetryService.validate_and_parse_csv(empty_bytes, filename="empty.csv")
    assert "empty (0 bytes)" in str(exc.value.detail)


def test_missing_required_columns_raises_exception():
    """Test 7: Ingesting a CSV missing mandatory sensor columns raises validation error."""
    # CSV with only machine ID and air temp, missing speed, torque, wear, process temp
    invalid_csv = b"Machine ID,Air temperature [K]\nCNC-01,298.5\n"
    with pytest.raises(TelemetryValidationException) as exc:
        TelemetryService.validate_and_parse_csv(invalid_csv, filename="missing_cols.csv")
    assert "Missing required telemetry columns" in str(exc.value.detail)


def test_non_finite_values_flagged():
    """Test 8: CSV with NaN, nulls, or infs is correctly flagged in validation."""
    csv_with_nan = (
        "Air temperature [K],Process temperature [K],Rotational speed [rpm],Torque [Nm],Tool wear [min]\n"
        "298.5,308.7,1500.0,NaN,45\n"
        "300.1,310.2,1480.0,42.0,50\n"
    ).encode("utf-8")

    df_valid, errors = TelemetryService.validate_and_parse_csv(csv_with_nan)
    assert len(df_valid) == 1  # Only the second row is valid
    assert any("NaN or infinite" in err for err in errors)


def test_out_of_range_values_flagged():
    """Test 8: Telemetry values violating physical operating envelopes are flagged."""
    # Impossible rotational speed: 99999 RPM
    csv_out_of_range = (
        "Air temperature [K],Process temperature [K],Rotational speed [rpm],Torque [Nm],Tool wear [min]\n"
        "298.5,308.7,99999.0,42.0,45\n"
    ).encode("utf-8")

    df_valid, errors = TelemetryService.validate_and_parse_csv(csv_out_of_range)
    assert len(df_valid) == 0
    assert any("outside plausible range" in err for err in errors)


def test_valid_sample_csv_ingestion(db_session):
    """Test 9: Verify valid sample CSV parses, enriches, and ingests without errors."""
    valid_csv = (
        "Machine Reference,Type,Air temperature [K],Process temperature [K],Rotational speed [rpm],Torque [Nm],Tool wear [min]\n"
        "CNC-MILL-01,M,298.5,308.7,1520.0,41.5,45\n"
        "CNC-MILL-02,L,301.2,310.5,1380.0,55.2,185\n"
    ).encode("utf-8")

    df_valid, errors = TelemetryService.validate_and_parse_csv(valid_csv)
    assert len(df_valid) == 2
    assert len(errors) == 0

    summary = TelemetryService.ingest_validated_df(db_session, df_valid, filename="test_sample.csv")
    assert summary.valid_records == 2
    assert summary.invalid_records == 0


def test_synthetic_telemetry_generation():
    """Test 10: Synthetic telemetry generator generates valid physics-based dataset."""
    df_synth = generate_synthetic_telemetry(n_samples=100, random_state=42)
    assert len(df_synth) == 100
    for col in CANONICAL_COLUMNS:
        assert col in df_synth.columns

    # Verify physical bounds
    assert df_synth["Air temperature [K]"].between(280.0, 320.0).all()
    assert (df_synth["Process temperature [K]"] >= df_synth["Air temperature [K]"]).all()
    assert df_synth["Rotational speed [rpm]"].between(1000.0, 3000.0).all()
    assert df_synth["Torque [Nm]"].between(3.0, 80.0).all()
    assert df_synth["Tool wear [min]"].between(0, 255).all()
