"""
IntelliMaint AI — PDF Generation & Reporting Tests
"""

from frontend.utils.pdf_generator import generate_inspection_pdf


def test_pdf_report_generation_and_structure():
    """Test 21: Generate PDF report and verify it is a valid, readable PDF document."""
    machine_info = {
        "machine_id": "CNC-MILL-02",
        "name": "Heavy Duty Vertical Machining Center",
        "machine_type": "CNC Milling Machine",
        "department": "Machining Cell Beta",
        "manufacturer": "Haas Automation",
        "operational_status": "DEGRADED",
    }
    telemetry_data = {
        "Air temperature [K]": 301.8,
        "Process temperature [K]": 310.2,
        "Rotational speed [rpm]": 1350.0,
        "Torque [Nm]": 62.4,
        "Tool wear [min]": 218.0,
    }
    risk_assessment = {
        "risk_category": "High",
        "failure_probability": 0.884,
        "model_version": "1.0.0",
    }
    contributing_factors = [
        {
            "factor": "Critical Cutting Edge Wear",
            "severity": "High",
            "value": "218 min",
            "impact": "Tool flank fracture hazard.",
        }
    ]
    actions = [
        "Replace cutting insert immediately.",
        "Inspect spindle runout and clean tool holder taper.",
    ]

    pdf_bytes = generate_inspection_pdf(
        machine_info=machine_info,
        telemetry_data=telemetry_data,
        risk_assessment=risk_assessment,
        contributing_factors=contributing_factors,
        recommended_actions=actions,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # Check standard PDF file signature
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_handles_empty_factors_gracefully():
    """Test 21: PDF generation does not fail when factor lists or actions are empty."""
    pdf_bytes = generate_inspection_pdf(
        machine_info={"machine_id": "EMPTY-01", "name": "Basic Asset"},
        telemetry_data={},
        risk_assessment={"risk_category": "Low", "failure_probability": 0.02},
        contributing_factors=[],
        recommended_actions=[],
    )
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")
