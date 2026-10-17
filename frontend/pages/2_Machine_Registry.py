"""
IntelliMaint AI — Machine Asset Registry (Page 2)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.components.ui_elements import apply_industrial_theme

st.set_page_config(page_title="Machine Registry | IntelliMaint AI", page_icon="⚙️", layout="wide")
apply_industrial_theme()

st.title("⚙️ Industrial Machine Asset Registry")
st.markdown("Register, track, search, and update industrial machinery across manufacturing cells.")

# Actions bar
a1, a2 = st.columns([3, 1])
with a2:
    if st.button("🔄 Reload Demo Machines", use_container_width=True):
        from scripts.seed_demo_data import seed_database
        seed_database(verbose=False)
        st.success("Demonstration machines refreshed!")
        st.rerun()

machines = api_client.get_machines()

# Form for registering a new machine
with st.expander("➕ Register New Industrial Machine", expanded=False):
    with st.form("new_machine_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_id = st.text_input("Machine Identifier * (e.g. CNC-MILL-05)", placeholder="CNC-MILL-05")
            new_name = st.text_input("Asset Name *", placeholder="High-Precision Milling Center")
            new_type = st.selectbox(
                "Equipment Category *",
                [
                    "CNC Milling Machine",
                    "CNC Turning Center",
                    "Hydraulic Power System",
                    "Industrial Robot",
                    "Pneumatics & Air System",
                    "Injection Molding Machine",
                    "Stamping Press",
                ],
            )
        with c2:
            new_dept = st.text_input("Facility Department / Cell", placeholder="Machining Cell Alpha")
            new_mfg = st.text_input("OEM Manufacturer", placeholder="DMG MORI")
            new_date = st.date_input("Installation Date", value=datetime.now())
            new_status = st.selectbox(
                "Initial Operational Status",
                ["OPERATIONAL", "DEGRADED", "MAINTENANCE", "OFFLINE"],
            )

        new_notes = st.text_area("Operational & Maintenance Notes", placeholder="Lubrication schedule, tooling specifications...")
        submitted = st.form_submit_button("Register Machine Asset", use_container_width=True)

        if submitted:
            if not new_id.strip() or not new_name.strip():
                st.error("Machine Identifier and Asset Name are required.")
            else:
                payload = {
                    "machine_id": new_id.strip().upper(),
                    "name": new_name.strip(),
                    "machine_type": new_type,
                    "department": new_dept.strip() if new_dept else None,
                    "manufacturer": new_mfg.strip() if new_mfg else None,
                    "installation_date": new_date.strftime("%Y-%m-%d"),
                    "operational_status": new_status,
                    "notes": new_notes.strip() if new_notes else None,
                }
                res = api_client.create_machine(payload)
                if "error" in res:
                    st.error(f"Failed to register machine: {res['error']}")
                else:
                    st.success(f"Machine '{new_id}' registered successfully!")
                    st.rerun()

st.markdown("### 🔍 Registered Fleet Assets")

# Search and Filters
f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    search_q = st.text_input("Search Assets", placeholder="Search by ID, name, or manufacturer...").lower()
with f2:
    status_filter = st.selectbox("Status Filter", ["All", "OPERATIONAL", "DEGRADED", "MAINTENANCE", "OFFLINE"])
with f3:
    type_options = ["All"] + sorted(list({m.get("machine_type") for m in machines if m.get("machine_type")}))
    type_filter = st.selectbox("Category Filter", type_options)

# Filter machines
filtered = machines
if search_q:
    filtered = [
        m for m in filtered
        if search_q in m.get("machine_id", "").lower()
        or search_q in m.get("name", "").lower()
        or search_q in (m.get("manufacturer") or "").lower()
    ]
if status_filter != "All":
    filtered = [m for m in filtered if m.get("operational_status") == status_filter]
if type_filter != "All":
    filtered = [m for m in filtered if m.get("machine_type") == type_filter]

st.caption(f"Showing {len(filtered)} of {len(machines)} total registered machines")

if filtered:
    df_m = pd.DataFrame(filtered)
    st.dataframe(
        df_m[["machine_id", "name", "machine_type", "department", "manufacturer", "installation_date", "operational_status", "notes"]],
        use_container_width=True,
        hide_index=True,
    )

    # Machine Detail & Deletion Section
    st.markdown("#### Manage Specific Machine")
    col_sel, col_del = st.columns([3, 1])
    with col_sel:
        target_machine = st.selectbox("Select Machine for Operations", [m["machine_id"] for m in filtered])
    with col_del:
        st.write("")
        st.write("")
        if st.button(f"🗑️ Delete {target_machine}", type="secondary"):
            if api_client.delete_machine(target_machine):
                st.success(f"Machine '{target_machine}' removed from registry.")
                st.rerun()
            else:
                st.error("Failed to delete machine.")
else:
    st.info("No machines match the selected filter criteria.")
