"""
IntelliMaint AI — Main Interactive Web Platform Entrypoint
"""

import sys
from pathlib import Path
import streamlit as st

# Setup path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.components.ui_elements import (
    apply_industrial_theme,
    render_metric_card,
    chart_risk_distribution,
)

st.set_page_config(
    page_title="IntelliMaint AI — Predictive Maintenance Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_industrial_theme()

# Sidebar Setup
with st.sidebar:
    st.markdown("## ⚡ IntelliMaint AI")
    st.caption("Industrial Predictive Maintenance & Asset Intelligence")
    
    # Check Connectivity
    health = api_client.check_backend_health()
    conn_mode = health.get("connection_mode", "DIRECT_DATABASE")
    
    if conn_mode == "FASTAPI_BACKEND":
        st.success("🟢 REST Backend: Connected (Port 8000)")
    else:
        st.info("🔵 Engine: Direct SQLite Mode (Port 8501)")

    st.markdown("---")
    st.markdown("### 🧭 Platform Navigation")
    st.markdown(
        """
        - [🏭 Fleet Dashboard](Fleet_Dashboard)
        - [⚙️ Machine Registry](Machine_Registry)
        - [📡 Upload & Analyze Telemetry](Upload_Analyze_Telemetry)
        - [🔍 Machine Risk Assessment](Machine_Risk_Assessment)
        - [📋 Maintenance Planner](Maintenance_Planner)
        - [📈 Analytics & Trends](Analytics_Trends)
        - [📑 Reports & History](Reports_Prediction_History)
        - [📘 About & Methodology](About_Methodology_Limitations)
        """
    )
    st.markdown("---")
    
    if st.button("🔄 Seed / Reset Demo Data", width="stretch"):
        from scripts.seed_demo_data import seed_database
        seed_database(verbose=False)
        st.success("Demo dataset seeded!")
        st.rerun()

    st.markdown("---")
    st.markdown("[📖 Interactive API Docs (OpenAPI)](http://127.0.0.1:8000/docs)")
    st.caption("Version 1.0.0 | Built for EEE Engineering Portfolio")


# Main Page Body
st.title("⚡ IntelliMaint AI — Intelligent Predictive Maintenance Platform")
st.markdown(
    '<div class="disclaimer-banner"><b>Engineering Platform:</b> Physics-grounded telemetry analytics, '
    'machine-learning failure risk estimation, and automated maintenance planning for industrial machine tools. '
    '(Educational and portfolio demonstration platform)</div>',
    unsafe_allow_html=True,
)

# Fleet summary quick glance
summary = api_client.get_fleet_summary()
total_machines = summary.get("total_registered_machines", 0)
high_risk = summary.get("high_risk_machines_count", 0)
med_risk = summary.get("medium_risk_machines_count", 0)
open_wo = summary.get("open_work_orders_count", 0)

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Registered Fleet", f"{total_machines} Assets", "Monitored industrial machines", "#0284C7")
with k2:
    render_metric_card("Critical Risk", f"{high_risk} Units", "High failure probability (>=65%)", "#EF4444")
with k3:
    render_metric_card("Elevated Watch", f"{med_risk} Units", "Early degradation advisory", "#F59E0B")
with k4:
    render_metric_card("Active Work Orders", f"{open_wo} Tasks", "Pending maintenance backlog", "#8B5CF6")

st.markdown("<br>", unsafe_allow_html=True)

# Architecture & Workflow Highlight
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("### 🏗️ End-to-End Predictive Maintenance Workflow")
    st.markdown(
        r"""
        1. **Telemetry Ingestion:** Real-time sensor acquisition of spindle speed (RPM), torque (Nm), cutting tool wear (min), and ambient vs. cutting process temperatures (Kelvin).
        2. **Physics Feature Engineering:** Calculation of Heat Dissipation Delta ($\Delta T = T_{proc} - T_{air}$), mechanical cutting power ($P = \omega \cdot \tau$), and mechanical strain products.
        3. **Machine Learning Inference:** Gradient Boosting / Random Forest ensemble models assess multi-modal degradation patterns based on the UCI AI4I 2020 benchmark.
        4. **Explainable Risk Scoring:** Provides root-cause diagnostic factors (e.g., tool flank fracture risk, coolant convection loss) and actionable maintenance advisories.
        5. **Closed-Loop Maintenance Work Orders:** Generates tracked work orders, technician dispatch schedules, and printable PDF inspection certificates.
        """
    )
with c2:
    risk_dist = summary.get("risk_distribution", {})
    if any(risk_dist.values()):
        st.plotly_chart(chart_risk_distribution(risk_dist), width="stretch")
    else:
        st.info("No risk distribution data available yet.")

st.markdown("---")
st.markdown("### 🚀 Quick Access Workspaces")

q1, q2, q3, q4 = st.columns(4)
with q1:
    st.markdown("#### 🏭 Fleet Dashboard")
    st.caption("Fleet-wide KPIs, real-time risk distribution, and machine health summaries.")
    if st.button("Go to Dashboard", width="stretch"):
        st.switch_page("pages/1_Fleet_Dashboard.py")

with q2:
    st.markdown("#### 🔍 Risk Assessment")
    st.caption("Interactive telemetry simulator with real-time ML risk scoring and PDF export.")
    if st.button("Run Risk Assessment", width="stretch"):
        st.switch_page("pages/4_Machine_Risk_Assessment.py")

with q3:
    st.markdown("#### 📡 Upload Telemetry")
    st.caption("Batch CSV ingestion, automated validation, and sensor operating envelopes.")
    if st.button("Upload Telemetry CSV", width="stretch"):
        st.switch_page("pages/3_Upload_Analyze_Telemetry.py")

with q4:
    st.markdown("#### 📋 Maintenance Planner")
    st.caption("Manage corrective work order lifecycle, technicians, and completion logs.")
    if st.button("Open Maintenance Planner", width="stretch"):
        st.switch_page("pages/5_Maintenance_Planner.py")
