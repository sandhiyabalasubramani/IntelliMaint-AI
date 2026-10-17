"""
IntelliMaint AI — Fleet Health Dashboard (Page 1)
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Setup path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.components.ui_elements import (
    apply_industrial_theme,
    render_metric_card,
    render_risk_badge,
    chart_risk_distribution,
    chart_machine_types,
)

st.set_page_config(page_title="Fleet Dashboard | IntelliMaint AI", page_icon="🏭", layout="wide")
apply_industrial_theme()

st.title("🏭 Industrial Fleet Health Dashboard")
st.markdown(
    '<div class="disclaimer-banner"><b>Operational Notice:</b> Real-time fleet health indicators derived from '
    'live database state and machine learning model inferences. (Educational & Portfolio Demonstration Platform)</div>',
    unsafe_allow_html=True,
)

# Fetch Fleet Summary
summary = api_client.get_fleet_summary()

total_machines = summary.get("total_registered_machines", 0)
high_risk = summary.get("high_risk_machines_count", 0)
med_risk = summary.get("medium_risk_machines_count", 0)
low_risk = summary.get("low_risk_machines_count", 0)
open_wo = summary.get("open_work_orders_count", 0)
comp_wo = summary.get("completed_work_orders_count", 0)
latest_ts = summary.get("latest_telemetry_timestamp") or "No telemetry yet"

if total_machines == 0:
    st.warning("No machines registered in the database yet. Click below to load demonstration assets!")
    if st.button("Load Demonstration Assets & Seed Data"):
        from scripts.seed_demo_data import seed_database
        seed_database(verbose=False)
        st.success("Demonstration machines, telemetry, and work orders seeded successfully!")
        st.rerun()

# KPI Metric Row
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_metric_card("Registered Fleet", f"{total_machines} Units", "Active industrial assets", "#0284C7")
with k2:
    render_metric_card("Critical Risk", f"{high_risk} Assets", "Immediate inspection recommended", "#EF4444")
with k3:
    render_metric_card("Elevated Risk", f"{med_risk} Assets", "Advisory degradation watch", "#F59E0B")
with k4:
    render_metric_card("Open Work Orders", f"{open_wo} Tasks", "Pending maintenance actions", "#8B5CF6")
with k5:
    render_metric_card("Completed Tasks", f"{comp_wo} Fixed", "Resolved work orders", "#10B981")

st.markdown("<br>", unsafe_allow_html=True)

# Charts Row
c1, c2 = st.columns([1, 1])
with c1:
    risk_dist = summary.get("risk_distribution", {})
    if any(risk_dist.values()):
        st.plotly_chart(chart_risk_distribution(risk_dist), use_container_width=True)
    else:
        st.info("No risk distribution data available.")

with c2:
    type_dist = summary.get("machine_type_distribution", {})
    if any(type_dist.values()):
        st.plotly_chart(chart_machine_types(type_dist), use_container_width=True)
    else:
        st.info("No equipment category data available.")

st.markdown("### 📋 Machine Risk & Operational Overview")

overview_data = summary.get("machine_risk_overview", [])
if overview_data:
    df_overview = pd.DataFrame(overview_data)
    
    # Format failure probability
    df_overview["latest_failure_prob"] = df_overview["latest_failure_prob"].apply(lambda p: f"{p:.1%}")
    df_overview.rename(
        columns={
            "machine_id": "Machine ID",
            "name": "Asset Name",
            "machine_type": "Equipment Category",
            "department": "Facility Cell",
            "operational_status": "Status",
            "latest_failure_prob": "Failure Prob",
            "latest_risk_tier": "Risk Tier",
            "open_work_orders_count": "Active WOs",
        },
        inplace=True,
    )
    
    # Display table
    st.dataframe(
        df_overview[["Machine ID", "Asset Name", "Equipment Category", "Facility Cell", "Status", "Failure Prob", "Risk Tier", "Active WOs"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No machine overview records to display.")
