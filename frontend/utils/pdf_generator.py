"""
IntelliMaint AI — Professional PDF Inspection & Maintenance Report Generator

Generates industrial maintenance reports with clean layouts, tabular summaries,
risk assessments, and compliance disclaimers using ReportLab.
"""

from __future__ import annotations
import io
from datetime import datetime, timezone
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_inspection_pdf(
    machine_info: Dict[str, Any],
    telemetry_data: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    contributing_factors: List[Dict[str, Any]],
    recommended_actions: List[str],
) -> bytes:
    """
    Builds a multi-section, publication-quality industrial maintenance PDF report.
    Returns bytes of the generated PDF document.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    bold_body = ParagraphStyle(
        "BoldBody",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748B"),
        fontName="Helvetica-Oblique",
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("INTELLIMAINT AI — INDUSTRIAL MAINTENANCE INSPECTION REPORT", title_style))
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph(f"Generated: {now_str} | Document ID: IMAI-{datetime.now().strftime('%Y%m%d%H%M%S')}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceAfter=12))

    # 2. Risk Executive Summary Badge Table
    risk_tier = risk_assessment.get("risk_category", risk_assessment.get("risk_tier", "Low"))
    risk_prob = risk_assessment.get("failure_probability", 0.0)

    # Color mapping
    tier_color = colors.HexColor("#10B981")  # Green for Low
    if risk_tier == "Medium":
        tier_color = colors.HexColor("#F59E0B")  # Amber
    elif risk_tier == "High":
        tier_color = colors.HexColor("#EF4444")  # Red

    risk_badge_data = [
        [
            Paragraph("<b>ASSESSMENT RESULT</b>", bold_body),
            Paragraph(f"<b>RISK TIER: <font color='{tier_color.hexval()}'>{risk_tier.upper()}</font></b>", bold_body),
            Paragraph(f"Failure Probability: <b>{risk_prob:.1%}</b>", bold_body),
            Paragraph(f"Model Version: <b>{risk_assessment.get('model_version', '1.0.0')}</b>", body_style),
        ]
    ]
    risk_table = Table(risk_badge_data, colWidths=[1.8 * inch, 2.0 * inch, 1.8 * inch, 1.8 * inch])
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 12))

    # 3. Machine & Asset Metadata
    story.append(Paragraph("1. Asset Identification & Operational Context", section_heading))
    asset_data = [
        [
            Paragraph("Machine Identifier:", bold_body),
            Paragraph(str(machine_info.get("machine_id", "N/A")), body_style),
            Paragraph("Equipment Name:", bold_body),
            Paragraph(str(machine_info.get("name", "N/A")), body_style),
        ],
        [
            Paragraph("Category / Type:", bold_body),
            Paragraph(str(machine_info.get("machine_type", "N/A")), body_style),
            Paragraph("Department / Bay:", bold_body),
            Paragraph(str(machine_info.get("department", "Facility Plant")), body_style),
        ],
        [
            Paragraph("Manufacturer:", bold_body),
            Paragraph(str(machine_info.get("manufacturer", "OEM Standard")), body_style),
            Paragraph("Operational Status:", bold_body),
            Paragraph(str(machine_info.get("operational_status", "OPERATIONAL")), body_style),
        ],
    ]
    asset_table = Table(asset_data, colWidths=[1.7 * inch, 2.0 * inch, 1.7 * inch, 2.0 * inch])
    asset_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(asset_table)
    story.append(Spacer(1, 10))

    # 4. Measured Telemetry & Derived Physics Indicators
    story.append(Paragraph("2. Operational Telemetry & Derived Engineering Indicators", section_heading))
    
    air_t = telemetry_data.get("Air temperature [K]", telemetry_data.get("air_temperature", 0.0))
    proc_t = telemetry_data.get("Process temperature [K]", telemetry_data.get("process_temperature", 0.0))
    speed = telemetry_data.get("Rotational speed [rpm]", telemetry_data.get("rotational_speed", 0.0))
    torque = telemetry_data.get("Torque [Nm]", telemetry_data.get("torque", 0.0))
    wear = telemetry_data.get("Tool wear [min]", telemetry_data.get("tool_wear", 0.0))

    delta_t = round(proc_t - air_t, 2)
    power = round((2.0 * 3.1415926535 * speed / 60.0) * torque, 2)
    strain = round(torque * wear, 2)

    telem_table_data = [
        [
            Paragraph("<b>Parameter</b>", bold_body),
            Paragraph("<b>Observed Value</b>", bold_body),
            Paragraph("<b>Derived Parameter</b>", bold_body),
            Paragraph("<b>Calculated Value</b>", bold_body),
        ],
        [
            Paragraph("Air Temperature", body_style),
            Paragraph(f"{air_t:.2f} K", body_style),
            Paragraph("Temperature Delta (ΔT)", body_style),
            Paragraph(f"{delta_t:.2f} K", body_style),
        ],
        [
            Paragraph("Process Temperature", body_style),
            Paragraph(f"{proc_t:.2f} K", body_style),
            Paragraph("Mechanical Power (P)", body_style),
            Paragraph(f"{power:.1f} W", body_style),
        ],
        [
            Paragraph("Rotational Speed", body_style),
            Paragraph(f"{speed:.1f} RPM", body_style),
            Paragraph("Strain Product (τ × wear)", body_style),
            Paragraph(f"{strain:.1f} Nm·min", body_style),
        ],
        [
            Paragraph("Spindle Torque", body_style),
            Paragraph(f"{torque:.2f} Nm", body_style),
            Paragraph("Tool Wear Duration", body_style),
            Paragraph(f"{wear:.0f} min", body_style),
        ],
    ]
    telem_table = Table(telem_table_data, colWidths=[2.0 * inch, 1.7 * inch, 2.0 * inch, 1.7 * inch])
    telem_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(telem_table)
    story.append(Spacer(1, 10))

    # 5. Contributing Failure Factors
    story.append(Paragraph("3. Model Diagnostics & Contributing Degradation Factors", section_heading))
    if contributing_factors:
        factors_rows = [
            [
                Paragraph("<b>Factor</b>", bold_body),
                Paragraph("<b>Severity</b>", bold_body),
                Paragraph("<b>Observed Condition</b>", bold_body),
                Paragraph("<b>Physical Impact</b>", bold_body),
            ]
        ]
        for f in contributing_factors:
            factors_rows.append([
                Paragraph(str(f.get("factor", "Anomaly")), body_style),
                Paragraph(str(f.get("severity", "Medium")), body_style),
                Paragraph(str(f.get("value", "N/A")), body_style),
                Paragraph(str(f.get("impact", "N/A")), body_style),
            ])
        factors_table = Table(factors_rows, colWidths=[1.8 * inch, 1.0 * inch, 1.8 * inch, 2.8 * inch])
        factors_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(factors_table)
    else:
        story.append(Paragraph("No critical degradation factors detected. Machine is operating inside normal statistical limits.", body_style))
    story.append(Spacer(1, 10))

    # 6. Actionable Maintenance Recommendations
    story.append(Paragraph("4. Recommended Engineering Actions", section_heading))
    if recommended_actions:
        for idx, act in enumerate(recommended_actions, 1):
            story.append(Paragraph(f"• <b>Action {idx}:</b> {act}", body_style))
            story.append(Spacer(1, 3))
    else:
        story.append(Paragraph("• Continue routine operational checks and planned predictive inspection schedule.", body_style))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94A3B8"), spaceAfter=8))

    # 7. Regulatory & Safety Disclaimer
    story.append(Paragraph(
        "<b>DISCLAIMER:</b> This inspection report is generated by the IntelliMaint AI academic and portfolio "
        "demonstration platform. Risk probabilities represent statistical estimations trained on machine learning models "
        "and physical telemetry indicators. This document does not constitute a certified industrial safety sign-off "
        "and must not supersede mandatory plant engineering protocols or OEM safety regulations.",
        disclaimer_style,
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
