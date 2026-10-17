"""
IntelliMaint AI — About, Methodology & System Limitations (Page 8)
"""

import sys
import json
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.components.ui_elements import apply_industrial_theme

st.set_page_config(page_title="About & Methodology | IntelliMaint AI", page_icon="📘", layout="wide")
apply_industrial_theme()

st.title("📘 About IntelliMaint AI — Methodology, Physics & Limitations")
st.markdown("Academic engineering documentation, physical failure modes, machine learning benchmark results, and system boundary conditions.")

# Section 1: Engineering Context
st.markdown("### 1. Problem Statement & Engineering Relevance")
st.write(
    """
    In modern high-speed automated manufacturing, unexpected spindle and tool failures result in catastrophic downtime, 
    scrapped precision workpieces, and millions of dollars in secondary machine tool damage. Traditional maintenance relies on 
    either **reactive maintenance** (fixing machines after breakdown) or **preventive maintenance** (replacing components on rigid, 
    calendar-based schedules, which frequently discards tooling with substantial remaining life).
    
    **IntelliMaint AI** integrates electrical sensor telemetry (motor current/torque, variable frequency drive rotational speed), 
    thermal dynamics (coolant heat dissipation), and mechanical wear physics into a unified predictive maintenance decision-support platform.
    """
)

# Section 2: Physical Failure Modes
st.markdown("### 2. Physical Failure Modes & Governing Laws (UCI AI4I 2020)")
m1, m2 = st.columns(2)
with m1:
    st.markdown(
        r"""
        - **Tool Wear Failure (TWF):** Progressive flank wear reaches micro-fracture limit (typically $\ge$ 200–240 minutes of accumulated cutting contact), leading to surface finish degradation and dimensional deviation.
        - **Heat Dissipation Failure (HDF):** Inadequate thermal convection when the temperature differential between process cutting zone and ambient air ($\Delta T = T_{proc} - T_{air}$) drops below 8.6 K at low spindle speeds (< 1380 RPM).
        - **Power Failure (PWF):** Electric motor drive operates outside nominal mechanical power envelope ($P = \omega \cdot \tau = \frac{2\pi \cdot \text{RPM}}{60} \cdot \tau$), indicating motor stall or drive overload (< 3500 W or > 9000 W).
        """
    )
with m2:
    st.markdown(
        r"""
        - **Overstrain Failure (OSF):** Extreme mechanical strain product ($\tau \times \text{Tool Wear}$) exceeding product design limits (11,000 to 13,000 $\text{Nm}\cdot\text{min}$), risking spindle arbor deflection.
        - **Random Failure (RNF):** Stochastic unmodeled environmental disturbances (~0.1% baseline incidence).
        """
    )

# Section 3: ML Pipeline & Actual Benchmark Metrics
st.markdown("### 3. Machine Learning Benchmark & Validation Results")
meta_file = BASE_DIR / "ml" / "models" / "model_metadata.json"
if meta_file.exists():
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    b1, b2, b3, b4 = st.columns(4)
    test_metrics = meta.get("test_metrics", {})
    with b1:
        st.metric("Champion Algorithm", meta.get("champion_algorithm", "Gradient Boosting"))
    with b2:
        st.metric("Test F1-Score", f"{test_metrics.get('f1_score', 0.0):.3f}")
    with b3:
        st.metric("PR-AUC (Avg Precision)", f"{test_metrics.get('pr_auc', 0.0):.3f}")
    with b4:
        st.metric("Test Precision / Recall", f"{test_metrics.get('precision', 0.0):.2f} / {test_metrics.get('recall', 0.0):.2f}")

    # Comparative benchmark table
    st.markdown("#### Candidate Model Benchmark Comparison")
    comp = meta.get("benchmark_comparison", {})
    if comp:
        df_comp = pd.DataFrame(comp).T
        st.dataframe(df_comp, use_container_width=True)

    # Feature importances
    st.markdown("#### Top Driving Model Features")
    fi = meta.get("feature_importances", {})
    if fi:
        df_fi = pd.DataFrame(list(fi.items()), columns=["Feature", "Importance Score"]).head(8)
        st.dataframe(df_fi, use_container_width=True, hide_index=True)
else:
    st.info("Model metadata file not yet created. Train model via ml/src/train.py.")

# Section 4: Operational Limitations & Disclaimer
st.markdown("### 4. Operational Boundaries & Safety Disclaimer")
st.markdown(
    """
    1. **Decision Support Only:** This application is engineered as an educational and portfolio demonstration system. Output failure probabilities are statistical estimations and **must not supersede certified industrial safety systems**, hardwired emergency stops (E-stops), or OEM machine tool manuals.
    2. **Probability vs. RUL:** A failure risk probability ($P$) is an instantaneous hazard indicator, not a deterministic guarantee of Remaining Useful Life (RUL) in hours.
    3. **Sensor Calibration:** Telemetry readings assume factory-calibrated RTDs, tachometers, and strain gauge dynamometers. Uncalibrated or noisy sensors will degrade inference confidence.
    """
)
