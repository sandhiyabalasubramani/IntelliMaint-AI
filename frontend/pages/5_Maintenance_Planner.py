"""
IntelliMaint AI — Maintenance Planner & Work Order Lifecycle (Page 5)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.utils.api_client import api_client
from frontend.components.ui_elements import apply_industrial_theme

st.set_page_config(page_title="Maintenance Planner | IntelliMaint AI", page_icon="📋", layout="wide")
apply_industrial_theme()

st.title("📋 Maintenance Work Order Planner & Lifecycle")
st.markdown("Track, dispatch, schedule, and resolve corrective and preventive maintenance tasks across the facility.")

machines = api_client.get_machines()
machine_ids = [m["machine_id"] for m in machines]

# Create New Work Order Form
with st.expander("➕ Create New Maintenance Work Order", expanded=False):
    with st.form("new_wo_form", clear_on_submit=True):
        w1, w2 = st.columns(2)
        with w1:
            wo_machine = st.selectbox("Associated Machine *", machine_ids if machine_ids else ["CNC-MILL-01"])
            wo_title = st.text_input("Work Order Title *", placeholder="Spindle Bearing Replacement & Vibration Calibration")
            wo_priority = st.selectbox("Priority Level", ["Low", "Medium", "High", "Critical"], index=1)
        with w2:
            wo_tech = st.text_input("Assigned Technician / Team", placeholder="Marcus Vance (Machining Tech)")
            wo_due = st.date_input("Target Due Date", value=datetime.now() + timedelta(days=3))
            wo_status = st.selectbox("Initial Status", ["Open", "In Progress"], index=0)

        wo_desc = st.text_area("Detailed Problem Statement & Scope", placeholder="Describe observed symptom, telemetry anomaly, or PM checklist...")
        submitted = st.form_submit_button("Dispatch Work Order", width="stretch")

        if submitted:
            if not wo_title.strip():
                st.error("Work Order Title is required.")
            else:
                payload = {
                    "machine_id": wo_machine,
                    "title": wo_title.strip(),
                    "description": wo_desc.strip() if wo_desc else None,
                    "priority": wo_priority,
                    "technician": wo_tech.strip() if wo_tech else None,
                    "due_date": wo_due.strftime("%Y-%m-%d"),
                    "status": wo_status,
                }
                res = api_client.create_maintenance_task(payload)
                if "error" in res:
                    st.error(f"Failed to create task: {res['error']}")
                else:
                    st.success(f"Work order '{res.get('work_order_no')}' registered successfully!")
                    st.rerun()

st.markdown("### 🛠️ Active Work Orders")

# Filters
f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    filter_status = st.selectbox("Filter Status", ["All", "Open", "In Progress", "Completed", "Cancelled"])
with f2:
    filter_priority = st.selectbox("Filter Priority", ["All", "Critical", "High", "Medium", "Low"])
with f3:
    filter_machine = st.selectbox("Filter Machine", ["All Machines"] + machine_ids)

status_arg = None if filter_status == "All" else filter_status
machine_arg = None if filter_machine == "All Machines" else filter_machine

tasks = api_client.get_maintenance_tasks(machine_id=machine_arg, status_filter=status_arg)
if filter_priority != "All":
    tasks = [t for t in tasks if t.get("priority") == filter_priority]

st.caption(f"Showing {len(tasks)} maintenance work orders")

if tasks:
    df_tasks = pd.DataFrame(tasks)
    st.dataframe(
        df_tasks[["work_order_no", "machine_id", "title", "priority", "status", "technician", "due_date", "created_at", "completed_at"]],
        width="stretch",
        hide_index=True,
    )

    st.markdown("#### Update Work Order Status")
    u1, u2, u3 = st.columns([2, 1, 1])
    with u1:
        selected_wo_no = st.selectbox("Select Work Order", [t["work_order_no"] for t in tasks])
    
    current_task = next((t for t in tasks if t["work_order_no"] == selected_wo_no), None)
    current_status = current_task.get("status", "Open") if current_task else "Open"

    # Enforce workflow state machine transitions in the UI
    allowed_transitions_map = {
        "Open": ["Open", "In Progress", "Cancelled"],
        "In Progress": ["In Progress", "Completed", "Cancelled", "Open"],
        "Completed": ["Completed", "In Progress"],
        "Cancelled": ["Cancelled", "Open"],
    }
    allowed_options = allowed_transitions_map.get(current_status, [current_status])
    if current_status not in allowed_options:
        allowed_options = [current_status] + allowed_options

    with u2:
        new_status = st.selectbox(
            "New Status",
            allowed_options,
            index=allowed_options.index(current_status) if current_status in allowed_options else 0,
            key=f"status_select_{selected_wo_no}",
            help=f"Current: {current_status}. Valid transitions: {', '.join(allowed_options)}",
        )
    with u3:
        st.write("")
        st.write("")
        update_btn = st.button("Apply Status Transition", width="stretch")

    resolution_notes = st.text_input(
        "Completion / Progress Notes",
        value=current_task.get("notes") or "",
        key=f"notes_input_{selected_wo_no}",
        placeholder="Add progress details, technician observations, or resolution summary...",
    )

    if update_btn and current_task:
        up_payload = {"status": new_status, "notes": resolution_notes}
        up_res = api_client.update_maintenance_task(selected_wo_no, up_payload)
        if "error" in up_res:
            st.error(f"Transition Error: {up_res['error']}")
        else:
            st.success(f"Work order '{selected_wo_no}' updated to '{new_status}'!")
            st.rerun()

else:
    st.info("No maintenance work orders match the selected filters.")
