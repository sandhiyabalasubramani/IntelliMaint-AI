"""
IntelliMaint AI — Advanced Analytics & Telemetry Trends (Page 6)
"""

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.components.ui_elements import (
    apply_industrial_theme,
    chart_speed_vs_torque,
    chart_temperature_delta,
    chart_tool_wear_histogram,
)

st.set_page_config(page_title="Analytics & Trends | IntelliMaint AI", page_icon="📈", layout="wide")
apply_industrial_theme()

st.title("📈 Advanced Fleet Analytics & Sensor Trends")
st.markdown("Deep-dive historical sensor distributions, operating envelopes, and failure mode patterns.")

telemetry = api_client.get_telemetry(limit=1000)
tasks = api_client.get_maintenance_tasks(limit=500)

if not telemetry:
    st.info("No telemetry records currently stored in the database. Ingest telemetry or run seed data.")
    st.stop()

df = pd.DataFrame(telemetry)

# Section 1: Mechanical Power vs Spindle Speed
st.markdown("### ⚡ Operating Envelope: Mechanical Power & Torque")
c1, c2 = st.columns(2)
with c1:
    fig_power = px.scatter(
        df,
        x="rotational_speed",
        y="mechanical_power",
        color="risk_tier",
        color_discrete_map={"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"},
        labels={"rotational_speed": "Rotational Speed (RPM)", "mechanical_power": "Mechanical Power (Watts)"},
        title="Rotational Speed vs Mechanical Power (P = ω · τ)",
    )
    # Nominal power boundaries 3500W - 9000W
    fig_power.add_hline(y=3500, line_dash="dash", line_color="#F59E0B", annotation_text="Min Power (3.5 kW)")
    fig_power.add_hline(y=9000, line_dash="dash", line_color="#EF4444", annotation_text="Max Power (9.0 kW)")
    fig_power.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
    st.plotly_chart(fig_power, width="stretch")

with c2:
    fig_strain = px.scatter(
        df,
        x="tool_wear",
        y="torque",
        color="risk_tier",
        color_discrete_map={"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"},
        labels={"tool_wear": "Tool Wear (min)", "torque": "Torque (Nm)"},
        title="Torque vs Tool Wear (Mechanical Overstrain Envelope)",
    )
    fig_strain.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
    st.plotly_chart(fig_strain, width="stretch")

# Section 2: Thermal Dynamics
st.markdown("### 🌡️ Thermal Dynamics & Heat Convection Analysis")
st.plotly_chart(chart_temperature_delta(df), width="stretch")

# Section 3: Work Order Priority Breakdown
if tasks:
    st.markdown("### 📋 Maintenance Backlog Dynamics")
    df_wo = pd.DataFrame(tasks)
    w1, w2 = st.columns(2)
    with w1:
        fig_wo_status = px.pie(
            df_wo,
            names="status",
            title="Work Orders by Operational Status",
            color="status",
            color_discrete_map={"Open": "#38BDF8", "In Progress": "#F59E0B", "Completed": "#10B981", "Cancelled": "#64748B"},
            hole=0.45,
        )
        fig_wo_status.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"))
        st.plotly_chart(fig_wo_status, width="stretch")
    with w2:
        fig_wo_prio = px.bar(
            df_wo,
            x="priority",
            color="priority",
            title="Work Orders by Priority Level",
            color_discrete_map={"Critical": "#EF4444", "High": "#F97316", "Medium": "#F59E0B", "Low": "#10B981"},
        )
        fig_wo_prio.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1"), showlegend=False)
        st.plotly_chart(fig_wo_prio, width="stretch")
