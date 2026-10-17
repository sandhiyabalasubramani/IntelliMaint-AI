"""
IntelliMaint AI — Frontend UI Styling & Chart Components
"""

from __future__ import annotations
from html import escape as html_escape
import re
from typing import Dict, Any, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


INDUSTRIAL_CSS = """
<style>
/* Modern Industrial Design Theme */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Metric card styling */
.metric-container {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    color: #F8FAFC;
    margin-bottom: 12px;
}
.metric-title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94A3B8;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #FFFFFF;
}
.metric-sub {
    font-size: 0.78rem;
    color: #38BDF8;
    margin-top: 4px;
}

/* Badges */
.badge-low {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10B981;
    border: 1px solid #10B981;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}
.badge-medium {
    background-color: rgba(245, 158, 11, 0.15);
    color: #F59E0B;
    border: 1px solid #F59E0B;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}
.badge-high {
    background-color: rgba(239, 68, 68, 0.15);
    color: #EF4444;
    border: 1px solid #EF4444;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}

/* Safety banner */
.disclaimer-banner {
    background-color: #1E293B;
    border-left: 4px solid #0284C7;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    font-size: 0.82rem;
    color: #CBD5E1;
    margin-bottom: 18px;
}
</style>
"""


def apply_industrial_theme():
    st.markdown(INDUSTRIAL_CSS, unsafe_allow_html=True)


def _safe_metric_color(color: str) -> str:
    """Accept only a six-digit hex color before placing it in inline CSS."""
    candidate = str(color or "")
    return candidate if re.fullmatch(r"#[0-9A-Fa-f]{6}", candidate) else "#334155"


def render_metric_card(title: str, value: Any, subtext: str = "", border_color: str = "#334155"):
    """Render a metric card while escaping dynamic text before HTML rendering."""
    safe_title = html_escape(str(title))
    safe_value = html_escape(str(value))
    safe_subtext = html_escape(str(subtext))
    safe_border_color = _safe_metric_color(border_color)

    st.markdown(
        f"""
        <div class="metric-container" style="border-top: 3px solid {safe_border_color};">
            <div class="metric-title">{safe_title}</div>
            <div class="metric-value">{safe_value}</div>
            <div class="metric-sub">{safe_subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_badge(tier: str) -> str:
    tier_lower = (tier or "low").lower()
    if "high" in tier_lower:
        return f'<span class="badge-high">CRITICAL RISK</span>'
    elif "medium" in tier_lower:
        return f'<span class="badge-medium">ELEVATED RISK</span>'
    else:
        return f'<span class="badge-low">NOMINAL HEALTH</span>'


# ================= PLOTLY CHART BUILDERS =================

def chart_risk_distribution(risk_dist: Dict[str, int]) -> go.Figure:
    labels = list(risk_dist.keys())
    values = list(risk_dist.values())
    color_map = {
        "Low": "#10B981",
        "Medium": "#F59E0B",
        "High": "#EF4444",
    }
    marker_colors = [color_map.get(k, "#94A3B8") for k in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=marker_colors),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        title="Fleet Failure Risk Classification",
        margin=dict(t=40, b=20, l=20, r=20),
        height=320,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
    )
    return fig


def chart_machine_types(type_dist: Dict[str, int]) -> go.Figure:
    df = pd.DataFrame(list(type_dist.items()), columns=["Category", "Count"])
    fig = px.bar(
        df,
        x="Count",
        y="Category",
        orientation="h",
        color="Count",
        color_continuous_scale="Blues",
        title="Equipment Registry by Category",
    )
    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
        coloraxis_showscale=False,
    )
    return fig


def chart_speed_vs_torque(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="rotational_speed",
        y="torque",
        color="risk_tier",
        color_discrete_map={"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"},
        size="tool_wear",
        hover_data=["machine_id"],
        labels={
            "rotational_speed": "Spindle Speed (RPM)",
            "torque": "Cutting Torque (Nm)",
            "risk_tier": "Risk Tier",
            "tool_wear": "Tool Wear (min)",
        },
        title="Operating Envelope: Spindle Speed vs. Torque (Bubble = Tool Wear)",
    )
    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
    )
    return fig


def chart_temperature_delta(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=df["air_temperature"],
            mode="lines+markers",
            name="Air Temp (K)",
            line=dict(color="#38BDF8"),
        )
    )
    fig.add_trace(
        go.Scatter(
            y=df["process_temperature"],
            mode="lines+markers",
            name="Process Temp (K)",
            line=dict(color="#F97316"),
        )
    )
    fig.update_layout(
        title="Thermal Operating Profiles (Process vs. Ambient Air)",
        xaxis_title="Telemetry Log Index",
        yaxis_title="Temperature (Kelvin)",
        margin=dict(t=40, b=20, l=20, r=20),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
    )
    return fig


def chart_tool_wear_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df,
        x="tool_wear",
        color="risk_tier",
        color_discrete_map={"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"},
        nbins=20,
        title="Tool Wear Duration Distribution (Minutes)",
        labels={"tool_wear": "Tool Wear (min)", "risk_tier": "Risk Category"},
    )
    # Threshold indicator at 200 min
    fig.add_vline(x=200, line_dash="dash", line_color="#EF4444", annotation_text="Wear Limit (200 min)")
    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
    )
    return fig
