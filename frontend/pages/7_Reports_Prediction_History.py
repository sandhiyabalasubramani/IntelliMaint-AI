"""
IntelliMaint AI — Reports & Prediction History (Page 7)
"""

import sys
import json
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.utils.pdf_generator import generate_inspection_pdf
from frontend.components.ui_elements import apply_industrial_theme

st.set_page_config(page_title="Reports & Prediction History | IntelliMaint AI", page_icon="📑", layout="wide")
apply_industrial_theme()

st.title("📑 Inspection Reports & Prediction History")
st.markdown("Audit historical machine learning assessments, export CSV audits, and compile PDF inspection certificates.")

machines = api_client.get_machines()
machine_ids = ["All Machines"] + [m["machine_id"] for m in machines]

# Filters
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    filter_m = st.selectbox("Filter by Machine Asset", machine_ids)
with c2:
    filter_tier = st.selectbox("Filter Risk Category", ["All", "High", "Medium", "Low"])
with c3:
    limit_val = st.number_input("Max Records", min_value=10, max_value=500, value=100, step=10)

m_arg = None if filter_m == "All Machines" else filter_m
predictions = api_client.get_predictions(machine_id=m_arg, limit=int(limit_val))

if filter_tier != "All":
    predictions = [p for p in predictions if p.get("risk_category") == filter_tier]

st.caption(f"Showing {len(predictions)} historical risk predictions")

if predictions:
    df_preds = pd.DataFrame(predictions)
    
    # CSV Export Button
    csv_bytes = df_preds.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export Filtered History to CSV",
        data=csv_bytes,
        file_name="intellimaint_prediction_audit.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("### 📜 Prediction Audit Trail")

    # Table
    table_cols = [
        "prediction_id",
        "machine_id",
        "timestamp",
        "failure_probability",
        "risk_category",
        "model_version",
        "model_algorithm",
    ]
    st.dataframe(df_preds[table_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🖨️ Compile & Download PDF Maintenance Certificate")

    p1, p2 = st.columns([3, 1])
    with p1:
        sel_pred_id = st.selectbox("Select Prediction ID for PDF Compilation", [p["prediction_id"] for p in predictions])
    
    target_pred = next((p for p in predictions if p["prediction_id"] == sel_pred_id), None)
    
    with p2:
        st.write("")
        st.write("")
        if target_pred:
            # Find machine details
            m_info = next((m for m in machines if m["machine_id"] == target_pred["machine_id"]), {
                "machine_id": target_pred["machine_id"],
                "name": f"Machine {target_pred['machine_id']}",
                "machine_type": "CNC Machining Center",
                "department": "Facility Floor",
                "operational_status": "OPERATIONAL",
            })

            # Mock or fetch telemetry
            telem_data = {
                "Air temperature [K]": 298.5,
                "Process temperature [K]": 308.7,
                "Rotational speed [rpm]": 1500.0,
                "Torque [Nm]": 42.0,
                "Tool wear [min]": 65.0,
            }

            pdf_bytes = generate_inspection_pdf(
                machine_info=m_info,
                telemetry_data=telem_data,
                risk_assessment=target_pred,
                contributing_factors=target_pred.get("contributing_factors", []),
                recommended_actions=target_pred.get("suggested_actions", []),
            )

            st.download_button(
                "📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Report_{target_pred['prediction_id']}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

else:
    st.info("No prediction records match the chosen filter.")
