"""
IntelliMaint AI — Interactive Machine Risk Assessment & Diagnostics (Page 4)
"""

import sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.utils.pdf_generator import generate_inspection_pdf
from frontend.components.ui_elements import (
    apply_industrial_theme,
    render_metric_card,
    render_risk_badge,
)

st.set_page_config(page_title="Machine Risk Assessment | IntelliMaint AI", page_icon="🔍", layout="wide")
apply_industrial_theme()

st.title("🔍 Real-Time Failure Risk Assessment & Diagnostics")
st.markdown("Perform physics-informed ML risk assessment, analyze contributing degradation factors, and dispatch maintenance work orders.")

machines = api_client.get_machines()
if not machines:
    st.warning("Please register a machine or seed demonstration data first.")
    st.stop()

machine_options = {f"{m['machine_id']} — {m['name']}": m for m in machines}
selected_label = st.selectbox("Select Target Industrial Machine", list(machine_options.keys()))
selected_machine = machine_options[selected_label]

st.markdown("#### Operational Telemetry Input Simulator")

# Presets to quickly showcase different engineering failure modes
preset = st.radio(
    "Load Operational Scenario Preset:",
    [
        "Nominal Operating Baseline (Low Risk)",
        "Severe Tool Flank Wear — TWF Mode (High Risk)",
        "Coolant Line Failure / Thermal Deficit — HDF Mode (High Risk)",
        "High Torque Heavy Roughing — OSF Mode (High Risk)",
    ],
    horizontal=True,
)

# Preset values
if preset == "Severe Tool Flank Wear — TWF Mode (High Risk)":
    init_air, init_proc, init_speed, init_torque, init_wear, init_type = 300.5, 310.8, 1420.0, 58.0, 225.0, "L"
elif preset == "Coolant Line Failure / Thermal Deficit — HDF Mode (High Risk)":
    init_air, init_proc, init_speed, init_torque, init_wear, init_type = 302.2, 308.1, 1340.0, 52.0, 85.0, "M"
elif preset == "High Torque Heavy Roughing — OSF Mode (High Risk)":
    init_air, init_proc, init_speed, init_torque, init_wear, init_type = 299.0, 309.5, 1310.0, 68.5, 195.0, "L"
else:
    init_air, init_proc, init_speed, init_torque, init_wear, init_type = 298.5, 308.7, 1530.0, 39.2, 45.0, "M"

c1, c2, c3 = st.columns(3)
with c1:
    air_temp = st.number_input("Ambient Air Temp (K)", min_value=250.0, max_value=350.0, value=float(init_air), step=0.1)
    proc_temp = st.number_input("Process / Cutting Temp (K)", min_value=250.0, max_value=360.0, value=float(init_proc), step=0.1)
with c2:
    speed = st.number_input("Spindle Rotational Speed (RPM)", min_value=500.0, max_value=5000.0, value=float(init_speed), step=10.0)
    torque = st.number_input("Spindle Torque (Nm)", min_value=0.0, max_value=150.0, value=float(init_torque), step=0.5)
with c3:
    wear = st.number_input("Cumulative Tool Wear (min)", min_value=0.0, max_value=500.0, value=float(init_wear), step=1.0)
    variant = st.selectbox("Tooling Variant Grade", ["L", "M", "H"], index=["L", "M", "H"].index(init_type))

# Run Assessment Button
if st.button("🚀 Execute Risk Assessment", type="primary", use_container_width=True):
    payload = {
        "machine_id": selected_machine["machine_id"],
        "air_temperature": air_temp,
        "process_temperature": proc_temp,
        "rotational_speed": speed,
        "torque": torque,
        "tool_wear": wear,
        "machine_type_variant": variant,
    }

    res = api_client.run_prediction(payload)
    if "error" in res:
        st.error(f"Assessment Failed: {res['error']}")
    else:
        st.session_state["latest_assessment"] = res
        st.session_state["latest_telemetry"] = payload

if "latest_assessment" in st.session_state:
    res = st.session_state["latest_assessment"]
    telem = st.session_state.get("latest_telemetry", {})
    
    st.markdown("---")
    st.markdown("### 📊 Assessment Findings & Failure Risk Analysis")

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        prob = res.get("failure_probability", 0.0)
        render_metric_card("Failure Probability", f"{prob:.1%}", f"Threshold P: {prob:.4f}", "#EF4444" if prob >= 0.65 else ("#F59E0B" if prob >= 0.25 else "#10B981"))
    with r2:
        tier = res.get("risk_category", "Low")
        border = "#EF4444" if tier == "High" else ("#F59E0B" if tier == "Medium" else "#10B981")
        render_metric_card("Classified Risk Tier", tier.upper(), "Decision Support Indicator", border)
    with r3:
        indicators = res.get("physical_indicators", {})
        delta_t = indicators.get("temp_diff_kelvin", round(proc_temp - air_temp, 2))
        render_metric_card("Thermal Delta (ΔT)", f"{delta_t:.1f} K", "Process minus Ambient", "#38BDF8")
    with r4:
        power = indicators.get("mechanical_power_watts", round((2 * 3.14159 * speed / 60.0) * torque, 1))
        render_metric_card("Mechanical Power", f"{power:.0f} W", "P = (2π·RPM/60) × Torque", "#8B5CF6")

    # Contributing Factors & Actions
    f_col, a_col = st.columns(2)
    with f_col:
        st.markdown("#### ⚠️ Principal Contributing Factors")
        factors = res.get("contributing_factors", [])
        if factors:
            for factor in factors:
                severity = factor.get("severity", "Medium")
                badge = "🔴" if severity == "High" else "🟡"
                st.markdown(f"**{badge} {factor.get('factor')}** ({factor.get('value')})")
                st.caption(f"Impact: {factor.get('impact')}")
        else:
            st.success("All observed parameters are within safe statistical tolerances.")

    with a_col:
        st.markdown("#### 🛠️ Suggested Maintenance Actions")
        actions = res.get("suggested_actions", [])
        for act in actions:
            st.markdown(f"- {act}")

    st.markdown("---")

    # Action dispatch and PDF export buttons
    b1, b2 = st.columns(2)
    with b1:
        # Create Maintenance Work Order from Assessment
        st.markdown("#### Dispatch Corrective Action")
        if st.button("📋 Create Work Order from this Risk Assessment", use_container_width=True):
            wo_payload = {
                "machine_id": selected_machine["machine_id"],
                "title": f"Corrective Action: {tier} Failure Risk on {selected_machine['machine_id']}",
                "description": (
                    f"Generated from ML Risk Assessment. Estimated Failure Probability: {prob:.1%}. "
                    f"Actions: {'; '.join(actions[:2])}"
                ),
                "priority": "Critical" if tier == "High" else ("High" if tier == "Medium" else "Low"),
                "status": "Open",
                "notes": f"Observed: Air Temp {air_temp}K, Proc Temp {proc_temp}K, RPM {speed}, Torque {torque}Nm, Wear {wear}min.",
            }
            wo_res = api_client.create_maintenance_task(wo_payload)
            if "error" in wo_res:
                st.error(f"Failed to create work order: {wo_res['error']}")
            else:
                st.success(f"Work order '{wo_res.get('work_order_no')}' dispatched to Maintenance Planner!")

    with b2:
        # Generate & Download PDF Report
        st.markdown("#### Export Documentation")
        pdf_bytes = generate_inspection_pdf(
            machine_info=selected_machine,
            telemetry_data=telem,
            risk_assessment=res,
            contributing_factors=res.get("contributing_factors", []),
            recommended_actions=res.get("suggested_actions", []),
        )
        st.download_button(
            "📄 Download PDF Inspection Report",
            data=pdf_bytes,
            file_name=f"Maintenance_Report_{selected_machine['machine_id']}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
