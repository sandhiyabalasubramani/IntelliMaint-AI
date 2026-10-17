"""
IntelliMaint AI — Telemetry Ingestion & Batch Risk Analytics (Page 3)
"""

import sys
from pathlib import Path
import pandas as pd
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

st.set_page_config(page_title="Upload & Analyze Telemetry | IntelliMaint AI", page_icon="📡", layout="wide")
apply_industrial_theme()

st.title("📡 Industrial Telemetry Ingestion & Batch Analytics")
st.markdown("Upload historical CSV sensor logs, validate physical operational limits, and execute automated batch failure-risk assessments.")

# Templates download section
t1, t2 = st.columns(2)
template_path = BASE_DIR / "ml" / "data" / "samples" / "sample_telemetry_template.csv"
demo_path = BASE_DIR / "ml" / "data" / "samples" / "sample_telemetry_demo.csv"

with t1:
    if template_path.exists():
        with open(template_path, "rb") as f:
            st.download_button(
                "📥 Download CSV Telemetry Template",
                data=f.read(),
                file_name="sample_telemetry_template.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Template CSV is generating...")

with t2:
    if demo_path.exists():
        with open(demo_path, "rb") as f:
            st.download_button(
                "📥 Download 60-Row Demonstration Dataset",
                data=f.read(),
                file_name="sample_telemetry_demo.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Demo CSV is generating...")

st.markdown("---")

uploaded_file = st.file_uploader(
    "Choose a Telemetry CSV File",
    type=["csv"],
    help="Accepts CSVs with columns: Air temperature [K], Process temperature [K], Rotational speed [rpm], Torque [Nm], Tool wear [min]",
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name

    st.info(f"Processing '{filename}' ({len(file_bytes) / 1024:.1f} KB)...")

    # Ingest and validate via client
    res = api_client.upload_telemetry_csv(file_bytes, filename=filename)

    if "error" in res:
        st.error(f"❌ Validation Failed: {res['error']}")
    else:
        st.success(f"✅ Telemetry validated and stored successfully!")
        
        # Ingestion metrics
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Total Records", res.get("total_records", 0))
        with s2:
            st.metric("High Risk Detected", res.get("high_risk_detected", 0))
        with s3:
            st.metric("Medium Risk", res.get("medium_risk_detected", 0))
        with s4:
            st.metric("Nominal / Low Risk", res.get("low_risk_detected", 0))

        if res.get("error_details"):
            with st.expander("⚠️ Validation Warnings & Adjusted Rows"):
                for err in res["error_details"]:
                    st.write(f"- {err}")

st.markdown("### 📊 Historical Telemetry Visualizer")

# Machine selection for visualization
machines = api_client.get_machines()
machine_ids = ["All Machines"] + [m["machine_id"] for m in machines]
selected_m = st.selectbox("Filter Telemetry by Machine", machine_ids)

filter_arg = None if selected_m == "All Machines" else selected_m
telemetry_data = api_client.get_telemetry(machine_id=filter_arg, limit=300)

if telemetry_data:
    df_telem = pd.DataFrame(telemetry_data)
    
    # Display Visualizations
    v1, v2 = st.columns(2)
    with v1:
        st.plotly_chart(chart_speed_vs_torque(df_telem), use_container_width=True)
    with v2:
        st.plotly_chart(chart_tool_wear_histogram(df_telem), use_container_width=True)

    st.plotly_chart(chart_temperature_delta(df_telem), use_container_width=True)

    st.markdown("#### Ingested Sensor Readings Table")
    display_cols = [
        "machine_id",
        "timestamp",
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "temp_diff",
        "mechanical_power",
        "risk_tier",
    ]
    present_cols = [c for c in display_cols if c in df_telem.columns]
    st.dataframe(df_telem[present_cols], use_container_width=True, hide_index=True)
else:
    st.info("No telemetry records found. Upload a CSV file or seed demo telemetry.")
