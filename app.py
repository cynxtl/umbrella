"""Umbrella 2.0: Context-Aware Weather Planning and Adaptive Decision-Making.

A premium SaaS-grade Streamlit application featuring:
- Dark atmospheric glassmorphism visual system
- Activity-aware weather planning
- Flagship Differentiator: Adaptive Plan Comparison
- Bounded LangGraph Planning Orchestrator with auditable execution trace
- 3 Collaborating Specialist Roles (Forecast Analyst, Risk Assessor, Planning Coordinator)
- Feedback-aware SQLite persistent memory + session memory
- Dark-styled Altair forecast analytics
- Safe credential injection (zero os.environ pollution)
"""
from __future__ import annotations

import os
import base64
import html
import uuid
from pathlib import Path
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import dotenv_values

from agent import (
    run_agent,
    build_demo_result,
    coordinate_recommendation,
    LOW_THRESHOLD,
    HIGH_THRESHOLD,
    tool_risk_assessment,
    tool_plan_comparison,
    generate_activity_recommendation,
)
import memory

ROOT = Path(__file__).resolve().parent

# Load local .env without overwriting global process environment
ENV_VARS = dotenv_values(ROOT / ".env")

st.set_page_config(
    page_title="Umbrella — Context-Aware Weather Planning",
    page_icon="☂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual System: Dark Atmospheric Glassmorphism ----------
st.markdown(
    """
<style>
:root {
    --color-midnight: #0B1020;
    --color-slate: #121B2E;
    --color-atmospheric: #182B46;
    --color-ice-blue: #82B9EB;
    --color-frost-white: #E8F3FF;
    --color-muted: #9BAEC6;
    --color-soft-green: #70C8A0;
    --color-soft-amber: #E9BF72;
    --color-muted-coral: #E88C8C;
}

/* Background composition */
.stApp {
    background: radial-gradient(circle at 18% 12%, rgba(24, 43, 70, 0.45) 0%, transparent 45%),
                radial-gradient(circle at 85% 80%, rgba(18, 27, 46, 0.6) 0%, transparent 50%),
                #0B1020;
    color: #E8F3FF;
}

[data-testid="stHeader"] {
    background: rgba(11, 16, 32, 0.85);
    backdrop-filter: blur(16px);
}

.block-container {
    max-width: 1440px;
    padding-top: 2.8rem;
    padding-bottom: 3.5rem;
}

[data-testid="stSidebar"] {
    background: #121B2E !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
}
[data-testid="stSidebar"] h3 {
    color: #E8F3FF;
    font-size: 0.98rem;
    letter-spacing: -0.015em;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #9BAEC6;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

/* Glassmorphism Surface Tokens */
.glass-panel {
    background: rgba(255, 255, 255, 0.045);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 20px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    padding: 22px 24px;
    margin-bottom: 18px;
}

.glass-card-compact {
    background: rgba(255, 255, 255, 0.035);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
    padding: 16px 18px;
    height: 100%;
}

/* Header & Hero */
.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
}
.brand-group {
    display: flex;
    align-items: center;
    gap: 14px;
}
.brand-group img {
    width: 44px;
    height: 44px;
    object-fit: contain;
}
.brand-text h1 {
    font-size: 1.45rem;
    font-weight: 800;
    margin: 0;
    color: #E8F3FF;
    letter-spacing: -0.03em;
    display: flex;
    align-items: center;
    gap: 8px;
}
.brand-text h1 span {
    color: #82B9EB;
}
.brand-text p {
    font-size: 0.78rem;
    color: #9BAEC6;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.hero-box {
    background: linear-gradient(135deg, rgba(24, 43, 70, 0.5) 0%, rgba(18, 27, 46, 0.7) 100%);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(130, 185, 235, 0.22);
    border-radius: 24px;
    padding: 26px 30px;
    margin-bottom: 22px;
    box-shadow: 0 16px 45px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
.hero-eyebrow {
    color: #82B9EB;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 6px;
}
.hero-title {
    font-size: clamp(1.8rem, 3.2vw, 2.6rem);
    font-weight: 850;
    line-height: 1.12;
    letter-spacing: -0.04em;
    color: #E8F3FF;
    margin: 0 0 8px 0;
}
.hero-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #9BAEC6;
    font-size: 0.95rem;
    margin-bottom: 18px;
    flex-wrap: wrap;
}

/* Badges & Pills */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 999px;
    padding: 4px 11px;
    font-weight: 750;
    letter-spacing: 0.04em;
    font-size: 0.72rem;
    text-transform: uppercase;
}
.pill-live { color: #70C8A0; background: rgba(112, 200, 160, 0.12); border: 1px solid rgba(112, 200, 160, 0.28); }
.pill-demo { color: #E9BF72; background: rgba(233, 191, 114, 0.12); border: 1px solid rgba(233, 191, 114, 0.28); }
.pill-low { color: #70C8A0; background: rgba(112, 200, 160, 0.14); border: 1px solid rgba(112, 200, 160, 0.3); }
.pill-moderate { color: #E9BF72; background: rgba(233, 191, 114, 0.14); border: 1px solid rgba(233, 191, 114, 0.3); }
.pill-high { color: #E88C8C; background: rgba(232, 140, 140, 0.14); border: 1px solid rgba(232, 140, 140, 0.3); }

/* Recommendation Banner */
.rec-card {
    border-radius: 18px;
    padding: 20px 22px;
    margin: 12px 0 16px;
    background: linear-gradient(135deg, rgba(130, 185, 235, 0.12) 0%, rgba(24, 43, 70, 0.25) 100%);
    border: 1px solid rgba(130, 185, 235, 0.3);
}
.rec-big {
    font-size: clamp(1.28rem, 2.2vw, 1.85rem);
    font-weight: 850;
    line-height: 1.22;
    letter-spacing: -0.035em;
    color: #E8F3FF;
}
.rec-support {
    color: #9BAEC6;
    font-size: 0.90rem;
    margin-top: 8px;
    line-height: 1.5;
}

/* Metric styling */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.038) !important;
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22) !important;
}
div[data-testid="stMetricLabel"] {
    color: #9BAEC6 !important;
    font-size: 0.78rem !important;
    font-weight: 600;
}
div[data-testid="stMetricValue"] {
    color: #E8F3FF !important;
    font-weight: 850 !important;
    letter-spacing: -0.03em !important;
}

/* Tabs & Inputs */
[data-testid="stTabs"] button[role="tab"] {
    color: #9BAEC6;
    font-weight: 750;
    font-size: 0.92rem;
    padding: 10px 18px;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #82B9EB !important;
    border-bottom: 2px solid #82B9EB !important;
}

.stTextInput input, .stSelectbox [data-baseweb="select"], .stTimeInput input {
    background: rgba(18, 27, 46, 0.75) !important;
    color: #E8F3FF !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
}
.stButton > button, .stFormSubmitButton > button {
    border-radius: 12px;
    font-weight: 750;
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #82B9EB 0%, #4D8BC9 100%) !important;
    color: #0B1020 !important;
    border: none !important;
    box-shadow: 0 4px 18px rgba(130, 185, 235, 0.28);
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #9AC7F2 0%, #5E9CE0 100%) !important;
    box-shadow: 0 6px 24px rgba(130, 185, 235, 0.42);
}

/* Adaptive Comparison Cards */
.comp-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin: 16px 0;
}
.plan-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(18px);
    border-radius: 18px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.09);
    position: relative;
}
.plan-card.recommended {
    border: 1px solid rgba(130, 185, 235, 0.45);
    background: linear-gradient(135deg, rgba(130, 185, 235, 0.09) 0%, rgba(24, 43, 70, 0.3) 100%);
    box-shadow: 0 10px 30px rgba(130, 185, 235, 0.12);
}
.plan-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.plan-title {
    font-size: 0.85rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9BAEC6;
}
.plan-time {
    font-size: 1.45rem;
    font-weight: 850;
    color: #E8F3FF;
    letter-spacing: -0.03em;
    margin-bottom: 6px;
}
.plan-pop {
    font-size: 2.1rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    color: #82B9EB;
}

/* Execution Trace & Role Cards */
.trace-step {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 14px 18px;
    margin: 8px 0;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
}
.trace-num {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 10px;
    background: rgba(130, 185, 235, 0.15);
    color: #82B9EB;
    font-weight: 850;
    font-size: 0.82rem;
    flex-shrink: 0;
}
.trace-title {
    font-size: 0.94rem;
    font-weight: 800;
    color: #E8F3FF;
}
.trace-desc {
    color: #9BAEC6;
    font-size: 0.82rem;
    margin-top: 3px;
}

/* Custom expanders, dataframes, insight notes */
.insight-note {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #9BAEC6;
    line-height: 1.55;
    font-size: 0.88rem;
}
.insight-note strong {
    color: #E8F3FF;
}
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.028) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Session State & Persistent Memory Sync ----------
stored_pref, stored_adj = memory.load_user_preference()

for key, default in {
    "weather_history": [],
    "last_result": None,
    "feedback_adjustment": stored_adj,
    "user_preference": stored_pref,
    "feedback_events": [],
    "last_location": "Pune",
    "activity_type": "College",
    "start_time": "09:00",
    "end_time": "16:00",
    "flexibility_hours": 2,
    "feedback_message": "",
    "api_key_owm_input": ENV_VARS.get("OPENWEATHER_API_KEY", ""),
    "api_key_groq_input": ENV_VARS.get("GROQ_API_KEY", ""),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def esc(value) -> str:
    return html.escape(str(value if value is not None else "—"), quote=True)


def to_display_temp(celsius: float, unit: str) -> float:
    return celsius if unit == "°C" else celsius * 9 / 5 + 32


def risk_for_probability(pop: float) -> str:
    if pop < LOW_THRESHOLD:
        return "LOW"
    if pop < HIGH_THRESHOLD:
        return "MODERATE"
    return "HIGH"


def get_risk_pill_html(risk: str) -> str:
    risk_upper = str(risk).upper()
    css = {
        "LOW": "pill-low",
        "MODERATE": "pill-moderate",
        "HIGH": "pill-high",
    }.get(risk_upper, "pill-moderate")
    return f'<span class="pill {css}">{esc(risk_upper)} RISK</span>'


def make_timeline(result: dict, unit: str) -> pd.DataFrame:
    rows = []
    for index, slot in enumerate(result.get("forecast_timeline") or []):
        probability = max(0.0, min(1.0, float(slot.get("rain_probability", 0.0))))
        celsius = float(slot.get("temperature", result.get("temperature", 0.0)))
        rows.append({
            "Slot": index + 1,
            "Time": str(slot.get("time", f"Slot {index + 1}")),
            "Rain probability (%)": round(probability * 100, 1),
            f"Temperature ({unit})": round(to_display_temp(celsius, unit), 1),
            "Conditions": str(slot.get("description", "Not specified")),
            "Risk band": risk_for_probability(probability),
        })
    return pd.DataFrame(rows)


def dark_rain_chart(frame: pd.DataFrame) -> alt.Chart:
    order = frame["Time"].tolist()
    base = alt.Chart(frame).encode(
        x=alt.X(
            "Time:N",
            sort=order,
            title=None,
            axis=alt.Axis(labelAngle=0, labelColor="#9BAEC6", tickSize=0, domain=False),
        ),
        tooltip=[
            alt.Tooltip("Time:N", title="Forecast time"),
            alt.Tooltip("Rain probability (%):Q", title="Rain probability", format=".1f"),
            alt.Tooltip("Risk band:N", title="Risk band"),
            alt.Tooltip("Conditions:N", title="Conditions"),
        ],
    )
    area = base.mark_area(
        color="#82B9EB",
        opacity=0.18,
        interpolate="monotone",
    ).encode(
        y=alt.Y(
            "Rain probability (%):Q",
            title="Chance of rain",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(
                labelColor="#9BAEC6",
                gridColor="rgba(255,255,255,0.07)",
                titleColor="#9BAEC6",
                ticks=False,
                domain=False,
            ),
        )
    )
    line = base.mark_line(
        color="#82B9EB",
        strokeWidth=3,
        point=alt.OverlayMarkDef(
            filled=True,
            fill="#E8F3FF",
            stroke="#82B9EB",
            strokeWidth=2,
            size=70,
        ),
        interpolate="monotone",
    ).encode(y="Rain probability (%):Q")

    moderate = (
        alt.Chart(pd.DataFrame({"threshold": [LOW_THRESHOLD * 100]}))
        .mark_rule(color="#E9BF72", strokeDash=[6, 4], strokeWidth=1.5)
        .encode(y="threshold:Q")
    )
    high = (
        alt.Chart(pd.DataFrame({"threshold": [HIGH_THRESHOLD * 100]}))
        .mark_rule(color="#E88C8C", strokeDash=[4, 4], strokeWidth=1.5)
        .encode(y="threshold:Q")
    )

    return (
        (area + line + moderate + high)
        .properties(height=280, background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            labelFont="sans-serif",
            titleFont="sans-serif",
            labelFontSize=11,
            titleFontSize=11,
        )
    )


def dark_temperature_chart(frame: pd.DataFrame, unit: str) -> alt.Chart:
    order = frame["Time"].tolist()
    temp_column = f"Temperature ({unit})"
    return (
        alt.Chart(frame)
        .mark_line(
            color="#70C8A0",
            strokeWidth=2.8,
            point=alt.OverlayMarkDef(
                filled=True,
                fill="#E8F3FF",
                stroke="#70C8A0",
                strokeWidth=2,
                size=60,
            ),
            interpolate="monotone",
        )
        .encode(
            x=alt.X(
                "Time:N",
                sort=order,
                title=None,
                axis=alt.Axis(labelAngle=0, labelColor="#9BAEC6", tickSize=0, domain=False),
            ),
            y=alt.Y(
                f"{temp_column}:Q",
                title=f"Temperature ({unit})",
                axis=alt.Axis(
                    labelColor="#9BAEC6",
                    titleColor="#9BAEC6",
                    gridColor="rgba(255,255,255,0.07)",
                    domain=False,
                    ticks=False,
                ),
            ),
            tooltip=[
                alt.Tooltip("Time:N", title="Forecast time"),
                alt.Tooltip(f"{temp_column}:Q", title="Temperature", format=".1f"),
                alt.Tooltip("Conditions:N", title="Conditions"),
            ],
        )
        .properties(height=240, background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            labelFont="sans-serif",
            titleFont="sans-serif",
            labelFontSize=11,
            titleFontSize=11,
        )
    )


def dark_risk_distribution_chart(frame: pd.DataFrame) -> alt.Chart:
    levels = ["LOW", "MODERATE", "HIGH"]
    counts = (
        frame["Risk band"]
        .value_counts()
        .reindex(levels, fill_value=0)
        .rename_axis("Risk band")
        .reset_index(name="Forecast slots")
    )
    return (
        alt.Chart(counts)
        .mark_bar(cornerRadiusEnd=6, size=24)
        .encode(
            y=alt.Y(
                "Risk band:N",
                sort=levels,
                title=None,
                axis=alt.Axis(labelColor="#9BAEC6", domain=False, ticks=False),
            ),
            x=alt.X(
                "Forecast slots:Q",
                title="Forecast slots (3h blocks)",
                axis=alt.Axis(
                    labelColor="#9BAEC6",
                    titleColor="#9BAEC6",
                    gridColor="rgba(255,255,255,0.07)",
                    ticks=False,
                    domain=False,
                ),
            ),
            color=alt.Color(
                "Risk band:N",
                scale=alt.Scale(domain=levels, range=["#70C8A0", "#E9BF72", "#E88C8C"]),
                legend=None,
            ),
            tooltip=["Risk band:N", "Forecast slots:Q"],
        )
        .properties(height=160, background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            labelFont="sans-serif",
            titleFont="sans-serif",
            labelFontSize=11,
            titleFontSize=11,
        )
    )


def append_history(result: dict, location: str, demo: bool):
    check_id = uuid.uuid4().hex[:10]
    result["_check_id"] = check_id
    pop = float(result.get("rain_probability", 0.0))
    risk = str(result.get("risk_level", "—"))
    rec = str(result.get("personalized_recommendation", result.get("recommendation", "—")))
    act_type = str(result.get("activity_type", "General"))
    start_t = str(result.get("start_time", ""))
    end_t = str(result.get("end_time", ""))

    entry = {
        "check_id": check_id,
        "location": location.strip(),
        "activity": act_type,
        "time_window": f"{start_t}–{end_t}" if start_t else "Full day",
        "rain_probability": pop,
        "risk_level": risk,
        "recommendation": rec,
        "checked_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "demo": bool(demo),
    }
    st.session_state.weather_history.append(entry)
    st.session_state.weather_history = st.session_state.weather_history[-25:]

    # Persist to SQLite memory asynchronously/safely
    memory.save_activity_record(
        location=location,
        activity_type=act_type,
        rain_probability=pop,
        risk_level=risk,
        recommendation=rec,
        start_time=start_t,
        end_time=end_t,
        is_demo=bool(demo),
    )


# ---------- Load Logo ----------
logo_path = ROOT / "umbrella_mark.svg"
if not logo_path.exists():
    logo_path = ROOT / "umbrella_logo.svg"
try:
    svg_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    logo_html = f'<img src="data:image/svg+xml;base64,{svg_b64}" alt="Umbrella Logo" />'
except OSError:
    logo_html = '<div style="font-size:2.4rem">☂️</div>'

# ---------- Top Navigation Bar ----------
st.markdown(
    f"""
<div class="app-header">
    <div class="brand-group">
        {logo_html}
        <div class="brand-text">
            <h1>umbrella<span>.</span></h1>
            <p>Planning Intelligence · Agentic AI System</p>
        </div>
    </div>
    <div style="display:flex; align-items:center; gap:10px;">
        <span class="pill pill-live">Agentic Orchestration</span>
        <span class="pill pill-demo">Deterministic Truth</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Settings & Credentials")
    st.caption("Safe credential injection: keys are passed to agent instances without altering process environment.")

    owm_key_input = st.text_input(
        "OpenWeather API key",
        value=st.session_state.api_key_owm_input,
        type="password",
        help="Required for live weather forecasts.",
    )
    st.session_state.api_key_owm_input = owm_key_input.strip()

    groq_key_input = st.text_input(
        "Groq API key (optional)",
        value=st.session_state.api_key_groq_input,
        type="password",
        help="Used to generate natural-language explanations without overriding decision logic.",
    )
    st.session_state.api_key_groq_input = groq_key_input.strip()

    st.divider()
    st.markdown("### Personalization")
    unit = st.radio("Temperature unit", ["°C", "°F"], horizontal=True, key="temperature_unit")
    preference = st.selectbox(
        "Advice style",
        ["Conservative", "Balanced", "Relaxed"],
        index=["Conservative", "Balanced", "Relaxed"].index(st.session_state.user_preference),
        help="Customizes personalized recommendation thresholds while leaving baseline risk intact.",
    )
    st.session_state.user_preference = preference

    adjustment = int(st.session_state.feedback_adjustment)
    if adjustment > 0:
        st.caption("⚡ Feedback memory: leaning one step more cautious")
    elif adjustment < 0:
        st.caption("⚡ Feedback memory: leaning one step more relaxed")
    else:
        st.caption("⚡ Feedback memory: standard selected style")

    st.divider()
    demo_mode = st.toggle("Offline jury demo", value=True, help="Simulates structured scenario data without external network calls.")
    if demo_mode:
        demo_scenario = st.selectbox("Demonstration scenario", ["Moderate", "Low", "High"], index=0)
        st.caption("Offline mode active: predictable, verified timelines for viva presentation.")
    else:
        demo_scenario = "Moderate"
        st.caption("Live mode: queries OpenWeather API using provided key.")

    st.divider()
    with st.expander("Deterministic Risk Rules", expanded=False):
        st.markdown(
            f"""
- **LOW:** Peak rain probability < {LOW_THRESHOLD:.0%}
- **MODERATE:** {LOW_THRESHOLD:.0%} to < {HIGH_THRESHOLD:.0%}
- **HIGH:** {HIGH_THRESHOLD:.0%} and above

*Rule:* Decision logic remains strictly deterministic. An LLM explains, but never decides or overrides classifications.
"""
        )

# ---------- Activity Planning Form ----------
with st.container():
    st.markdown('<div class="hero-eyebrow">Context-Aware Activity Planner</div>', unsafe_allow_html=True)
    with st.form("planning_form", clear_on_submit=False):
        row1_col1, row1_col2, row1_col3 = st.columns([1.4, 1.2, 1.2])
        with row1_col1:
            location_val = st.text_input(
                "Destination / City",
                value=st.session_state.last_location,
                placeholder="e.g. Pune, IN",
            )
        with row1_col2:
            activity_options = ["College", "Office commute", "Walking", "Outdoor event", "Travel", "Custom activity"]
            act_idx = activity_options.index(st.session_state.activity_type) if st.session_state.activity_type in activity_options else 0
            activity_val = st.selectbox("Activity Type", activity_options, index=act_idx)
        with row1_col3:
            flex_options = [0, 1, 2, 3, 4]
            flex_val = st.selectbox(
                "Allowed Schedule Flexibility",
                flex_options,
                index=flex_options.index(st.session_state.flexibility_hours) if st.session_state.flexibility_hours in flex_options else 2,
                format_func=lambda x: "Fixed timing (±0h)" if x == 0 else f"±{x} hours flexible",
                help="Allows Adaptive Plan Comparison to evaluate lower-risk alternative time windows.",
            )

        row2_col1, row2_col2, row2_col3 = st.columns([1, 1, 1.2], vertical_alignment="bottom")
        with row2_col1:
            start_val = st.text_input("Start Time", value=st.session_state.start_time, help="e.g. 09:00 or 9:00 AM")
        with row2_col2:
            end_val = st.text_input("End Time", value=st.session_state.end_time, help="e.g. 16:00 or 4:00 PM")
        with row2_col3:
            submitted = st.form_submit_button("Plan & Evaluate Weather  →", type="primary", use_container_width=True)

if submitted:
    if not location_val.strip():
        st.warning("Please provide a city name or location.")
    elif not demo_mode and not st.session_state.api_key_owm_input:
        st.error("OpenWeather API key is required for live forecasts. Add your key in the sidebar or toggle Offline jury demo.")
    else:
        st.session_state.last_location = location_val.strip()
        st.session_state.activity_type = activity_val
        st.session_state.start_time = start_val.strip()
        st.session_state.end_time = end_val.strip()
        st.session_state.flexibility_hours = flex_val

        with st.spinner("Umbrella Planning Orchestrator executing agent workflow…"):
            agent_result = run_agent(
                location=location_val.strip(),
                preference=preference,
                caution_adjustment=int(st.session_state.feedback_adjustment),
                activity_type=activity_val,
                start_time=start_val.strip(),
                end_time=end_val.strip(),
                flexibility_hours=flex_val,
                api_key_owm=st.session_state.api_key_owm_input,
                api_key_groq=st.session_state.api_key_groq_input,
                demo_mode=demo_mode,
                demo_scenario=demo_scenario,
            )

        if agent_result.get("error") and agent_result.get("rain_probability") is None:
            st.error(agent_result.get("explanation") or "Forecast lookup failed.")
        else:
            st.session_state.last_result = agent_result
            append_history(agent_result, location_val.strip(), demo_mode)

# ---------- Render Main Product Dashboard ----------
result = st.session_state.last_result

if not result:
    # Initial state if not yet queried
    # Run default demo query on first load to give immediate premium experience
    result = run_agent(
        location="Pune",
        preference=st.session_state.user_preference,
        caution_adjustment=int(st.session_state.feedback_adjustment),
        activity_type=st.session_state.activity_type,
        start_time=st.session_state.start_time,
        end_time=st.session_state.end_time,
        flexibility_hours=st.session_state.flexibility_hours,
        demo_mode=True,
        demo_scenario="Moderate",
    )
    st.session_state.last_result = result
    append_history(result, "Pune", True)

is_demo = bool(result.get("demo_mode"))
loc_name = str(result.get("location", st.session_state.last_location))
act_name = str(result.get("activity_type", st.session_state.activity_type))
start_t = str(result.get("start_time", st.session_state.start_time))
end_t = str(result.get("end_time", st.session_state.end_time))
full_pop = max(0.0, min(1.0, float(result.get("rain_probability", 0.0))))
full_risk = str(result.get("risk_level", "MODERATE")).upper()

act_analysis = result.get("activity_analysis") or {}
act_pop = max(0.0, min(1.0, float(act_analysis.get("peak_pop", full_pop))))
act_risk = str(act_analysis.get("risk_level", full_risk)).upper()
temp_c = float(result.get("temperature", 0.0))
temp_display = to_display_temp(temp_c, unit)
wind_spd = float(result.get("wind_speed", 4.2))

frame = make_timeline(result, unit)
slot_count = len(frame)
mean_pop = float(frame["Rain probability (%)"].mean() / 100) if slot_count else full_pop
temp_col = f"Temperature ({unit})"
temp_min = float(frame[temp_col].min()) if slot_count else temp_display
temp_max = float(frame[temp_col].max()) if slot_count else temp_display
mod_slots = int((frame["Rain probability (%)"] >= LOW_THRESHOLD * 100).sum()) if slot_count else 0
high_slots = int((frame["Rain probability (%)"] >= HIGH_THRESHOLD * 100).sum()) if slot_count else 0

comp_data = result.get("plan_comparison") or {}
action_rec = result.get("personalized_recommendation", result.get("recommendation", "Carry an umbrella just in case"))

# Hero Component: Daily Outlook & Actionable Decision
st.markdown(
    f"""
<div class="hero-box">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
        <div>
            <div class="hero-eyebrow">Tomorrow's Daily Outlook · {esc(result.get("forecast_date", "Pune"))}</div>
            <div class="hero-title">Tomorrow in {esc(loc_name)}</div>
            <div class="hero-meta">
                <span>🎯 {esc(act_name)} ({esc(start_t)} – {esc(end_t)})</span>
                <span>·</span>
                <span>🌤️ {esc(act_analysis.get("conditions", result.get("description", "Partly cloudy")))}</span>
                <span>·</span>
                {get_risk_pill_html(act_risk)}
            </div>
        </div>
        <div>
            <span class="pill {'pill-demo' if is_demo else 'pill-live'}">
                {'🧪 OFFLINE DEMO' if is_demo else '⚡ LIVE SATELLITE FORECAST'}
            </span>
        </div>
    </div>
    <div class="rec-card">
        <div class="hero-eyebrow" style="color:#82B9EB">Primary Recommendation</div>
        <div class="rec-big">{esc(action_rec)}</div>
        <div class="rec-support">
            Activity window overlaps with {act_pop:.0%} rain probability ({act_risk} risk).
            Personalized with {esc(result.get("effective_preference", preference)).lower()} advice styling.
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Four Compact High-Signal Metric Cards
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Peak Rain Probability", f"{act_pop:.0%}", help="Peak rain risk during your requested activity window.")
m_col2.metric("Peak Risk Period", result.get("peak_time_short", "3:00 PM"), help="Time slot with the highest expected precipitation.")
m_col3.metric("Temperature Range", f"{temp_min:.0f}–{temp_max:.0f}{unit}", help="Daily minimum to maximum temperature across forecast slots.")
m_col4.metric("Wind & Conditions", f"{wind_spd:.1f} m/s", help=f"Expected condition: {result.get('description', 'Clear')}")

# ---------- Six Main Application Sections ----------
tab_overview, tab_planner, tab_compare, tab_analytics, tab_agent, tab_memory = st.tabs([
    "Overview",
    "Activity Planner",
    "Compare Plans",
    "Forecast Analytics",
    "Agent Intelligence",
    "Memory & History",
])

# ==================== 1. OVERVIEW ====================
with tab_overview:
    ov_left, ov_right = st.columns([1.1, 1.4], gap="medium")
    with ov_left:
        with st.container():
            st.markdown(
                f"""
<div class="glass-panel">
    <div class="hero-eyebrow">Deterministic Baseline Decision</div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
        <div style="font-size:1.15rem; font-weight:800; color:#E8F3FF;">
            {esc(result.get("recommendation", "—"))}
        </div>
        {get_risk_pill_html(full_risk)}
    </div>
    <div style="color:#9BAEC6; font-size:0.85rem; margin-top:8px;">
        Evaluated on full-day peak rain probability ({full_pop:.0%}).
        Baseline thresholds: LOW &lt;30% · MODERATE 30%–&lt;60% · HIGH ≥60%.
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

        with st.container():
            st.markdown(
                f"""
<div class="glass-panel">
    <div class="hero-eyebrow">Peak Period Weather Facts</div>
    <div style="font-size:1.9rem; font-weight:900; color:#E8F3FF; letter-spacing:-0.03em; margin:6px 0;">
        {temp_display:.1f}{unit}
    </div>
    <div style="color:#9BAEC6; font-size:0.92rem;">
        {esc(result.get("description", "Clear sky"))}
    </div>
    <div style="color:#82B9EB; font-size:0.82rem; margin-top:6px;">
        Peak slot: {esc(result.get("peak_rain_time", result.get("peak_time_short", "Tomorrow")))}
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

    with ov_right:
        with st.container():
            st.markdown('<div class="hero-eyebrow">Tomorrow At A Glance</div>', unsafe_allow_html=True)
            if slot_count:
                st.altair_chart(dark_rain_chart(frame), use_container_width=True)
            else:
                st.info("No timeline data returned for this location.")

    with st.container():
        st.markdown(
            f"""
<div class="insight-note">
    <strong>Forecast Insights:</strong> {mod_slots} of {slot_count} forecast slots reach at least moderate rain risk ({LOW_THRESHOLD:.0%}).
    The average slot probability is {mean_pop:.0%} (arithmetic mean across slots, not cumulative rain risk).
    Temperature ranges between {temp_min:.1f}{unit} and {temp_max:.1f}{unit}.
</div>
""",
            unsafe_allow_html=True,
        )

    with st.expander("AI & Rule-Based Explanation", expanded=False):
        st.write(result.get("explanation", "Summary unavailable."))
        if not result.get("llm_available"):
            st.caption("Language model was offline or unconfigured; deterministic rule-based explainer was utilized.")

# ==================== 2. ACTIVITY PLANNER ====================
with tab_planner:
    st.markdown('<div class="hero-eyebrow">Context-Aware Activity Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-note">
    Evaluating conditions specifically during your activity window: <strong>{esc(act_name)} ({esc(start_t)} – {esc(end_t)})</strong>.
    OpenWeather provides 3-hour interval slots; Umbrella accurately maps your requested window across overlapping intervals.
</div>
""",
        unsafe_allow_html=True,
    )

    act_col1, act_col2 = st.columns([1, 1], gap="medium")
    with act_col1:
        with st.container():
            st.markdown(
                f"""
<div class="glass-panel">
    <div class="hero-eyebrow">Activity Window Risk</div>
    <div style="font-size:2.2rem; font-weight:900; color:#82B9EB; margin:8px 0;">
        {act_pop:.0%}
    </div>
    <div style="display:flex; gap:8px; align-items:center; margin-bottom:12px;">
        {get_risk_pill_html(act_risk)}
        <span style="color:#9BAEC6; font-size:0.85rem;">during {esc(act_name)}</span>
    </div>
    <div style="color:#E8F3FF; font-weight:750; font-size:0.98rem;">
        {esc(action_rec)}
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

    with act_col2:
        with st.container():
            overlapping_slots = act_analysis.get("overlapping_slots") or []
            slot_names = ", ".join([str(s.get("time")) for s in overlapping_slots]) or "All slots"
            st.markdown(
                f"""
<div class="glass-panel">
    <div class="hero-eyebrow">Window Coverage & Details</div>
    <div style="color:#E8F3FF; font-size:0.95rem; margin-top:8px;">
        <strong>Overlapping Slots:</strong> {esc(slot_names)}
    </div>
    <div style="color:#9BAEC6; font-size:0.88rem; margin-top:6px;">
        <strong>Moderate/High Risk Slots in Window:</strong> {act_analysis.get("moderate_slots", 0)} moderate, {act_analysis.get("high_slots", 0)} high.
    </div>
    <div style="color:#9BAEC6; font-size:0.88rem; margin-top:6px;">
        <strong>Window Temperature:</strong> {act_analysis.get("temp_min", 20):.1f}°C to {act_analysis.get("temp_max", 23):.1f}°C.
    </div>
    <div style="color:#9BAEC6; font-size:0.88rem; margin-top:6px;">
        <strong>Peak Wind Speed:</strong> {act_analysis.get("wind_speed_max", 4.0):.1f} m/s.
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

# ==================== 3. COMPARE PLANS (FLAGSHIP) ====================
with tab_compare:
    st.markdown('<div class="hero-eyebrow">Flagship Feature · Adaptive Plan Comparison</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="insight-note">
    Umbrella evaluates alternative feasible time windows within your allowed scheduling flexibility (± hours).
    When conditions improve significantly, it recommends shifting your activity to avoid rain peaks.
</div>
""",
        unsafe_allow_html=True,
    )

    orig_p = comp_data.get("original_plan") or {}
    rec_p = comp_data.get("recommended_plan") or orig_p
    has_alt = bool(comp_data.get("has_better_alternative"))
    reduction = float(comp_data.get("risk_reduction_pp", 0.0))

    comp_left, comp_right = st.columns(2, gap="medium")
    with comp_left:
        orig_risk = orig_p.get("risk_level", "MODERATE")
        orig_pop = float(orig_p.get("peak_pop", 0.0))
        st.markdown(
            f"""
<div class="plan-card">
    <div class="plan-header">
        <span class="plan-title">Original Plan</span>
        {get_risk_pill_html(orig_risk)}
    </div>
    <div class="plan-time">{esc(orig_p.get("label", "Selected time"))}</div>
    <div class="plan-pop">{orig_pop:.0%} <span style="font-size:1rem; color:#9BAEC6; font-weight:600">peak rain risk</span></div>
    <div style="color:#9BAEC6; font-size:0.88rem; margin-top:8px;">
        Conditions: {esc(orig_p.get("conditions", "Not specified"))} · {esc(orig_p.get("temp_range", ""))}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with comp_right:
        rec_risk = rec_p.get("risk_level", orig_risk)
        rec_pop = float(rec_p.get("peak_pop", orig_pop))
        st.markdown(
            f"""
<div class="plan-card recommended">
    <div class="plan-header">
        <span class="plan-title">{'Recommended Alternative' if has_alt else 'Optimal Plan Confirmed'}</span>
        {get_risk_pill_html(rec_risk)}
    </div>
    <div class="plan-time">{esc(rec_p.get("label", "Recommended time"))}</div>
    <div class="plan-pop">{rec_pop:.0%} <span style="font-size:1rem; color:#9BAEC6; font-weight:600">peak rain risk</span></div>
    <div style="color:#9BAEC6; font-size:0.88rem; margin-top:8px;">
        Conditions: {esc(rec_p.get("conditions", "Not specified"))} · {esc(rec_p.get("temp_range", ""))}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Decision Evidence Panel
    verdict_badge = '<span class="pill pill-live">LOWER-RISK WINDOW IDENTIFIED</span>' if has_alt else '<span class="pill pill-demo">ORIGINAL TIMING OPTIMAL</span>'
    st.markdown(
        f"""
<div class="glass-panel" style="margin-top:14px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div class="hero-eyebrow">Agent Decision Evidence · Why this plan?</div>
        {verdict_badge}
    </div>
    <div style="font-size:1.05rem; font-weight:750; color:#E8F3FF; line-height:1.5;">
        {esc(comp_data.get("why_this_plan", "Evaluation completed."))}
    </div>
    <div style="color:#9BAEC6; font-size:0.85rem; margin-top:10px;">
        Candidate windows evaluated: {comp_data.get("candidates_evaluated", 1)} feasible options within allowed flexibility.
        {f'Risk reduction: <strong>{reduction:.1f} percentage points</strong> lower probability.' if has_alt else ''}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    candidates_list = comp_data.get("candidates") or []
    if len(candidates_list) > 1:
        with st.expander("Inspect All Evaluated Candidate Windows", expanded=False):
            cand_rows = []
            for c in candidates_list:
                cand_rows.append({
                    "Window": c.get("label"),
                    "Peak Rain Risk": f"{c.get('peak_pop', 0):.0%}",
                    "Risk Band": c.get("risk_level"),
                    "Conditions": c.get("conditions"),
                    "Temperature": c.get("temp_range"),
                })
            st.dataframe(pd.DataFrame(cand_rows), use_container_width=True, hide_index=True)

# ==================== 4. FORECAST ANALYTICS ====================
with tab_analytics:
    st.markdown('<div class="hero-eyebrow">Dark Analytical Visualizations</div>', unsafe_allow_html=True)
    c_left, c_right = st.columns([1.4, 1], gap="medium")
    with c_left:
        with st.container():
            st.markdown("### Rain Probability Curve")
            st.caption("3-hour forecast slots. Dashed rules mark 30% (Moderate, Amber) and 60% (High, Coral) thresholds.")
            if slot_count:
                st.altair_chart(dark_rain_chart(frame), use_container_width=True)
    with c_right:
        with st.container():
            st.markdown("### Risk Band Distribution")
            st.caption("Number of forecast slots in each baseline risk category.")
            if slot_count:
                st.altair_chart(dark_risk_distribution_chart(frame), use_container_width=True)

    t_left, t_right = st.columns([1.2, 1], gap="medium")
    with t_left:
        with st.container():
            st.markdown("### Temperature Trend")
            st.caption(f"Diurnal temperature curve ({unit}).")
            if slot_count:
                st.altair_chart(dark_temperature_chart(frame, unit), use_container_width=True)
    with t_right:
        with st.container():
            st.markdown("### Slot-by-Slot Detail")
            if slot_count:
                visible = frame[["Time", "Rain probability (%)", temp_col, "Risk band", "Conditions"]].copy()
                visible["Rain probability (%)"] = visible["Rain probability (%)"].map(lambda v: f"{v:.0f}%")
                visible[temp_col] = visible[temp_col].map(lambda v: f"{v:.1f}°")
                st.dataframe(visible, use_container_width=True, hide_index=True, height=240)

    st.caption("Interpretation note: Forecast-slot probabilities are not cumulative and must not be added together.")

# ==================== 5. AGENT INTELLIGENCE ====================
with tab_agent:
    st.markdown('<div class="hero-eyebrow">LangGraph Planning Orchestrator Execution Trace</div>', unsafe_allow_html=True)
    st.caption("Real, auditable chronological execution trace showing genuine tool inputs, outputs, and status.")

    traces = result.get("execution_trace") or []
    for step in traces:
        s_num = step.get("step", "—")
        s_title = step.get("title", "Action")
        s_node = step.get("tool_or_node", "Node")
        s_status = step.get("status", "SUCCESS")
        s_dur = step.get("duration_ms", 0.0)
        s_in = step.get("inputs", {})
        s_out = step.get("outputs", {})

        st.markdown(
            f"""
<div class="trace-step">
    <div class="trace-num">{s_num}</div>
    <div style="flex-grow:1">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="trace-title">{esc(s_title)} <span style="color:#9BAEC6; font-weight:400; font-size:0.8rem">({esc(s_node)})</span></div>
            <span class="pill pill-live">{esc(s_status)} · {s_dur}ms</span>
        </div>
        <div class="trace-desc">
            Inputs: <code>{esc(str(s_in))}</code><br>
            Outputs: <code>{esc(str(s_out))}</code>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("### Three Collaborating Specialist Roles")
    analyst_o = result.get("analyst_output") or {}
    assessor_o = result.get("assessor_output") or {}
    coord_o = result.get("coordinator_output") or {}
    roles_info = [
        ("01", "Forecast Analyst", f"Parsed {analyst_o.get('slots_reviewed', slot_count)} slots; peak rain {full_pop:.0%} at {result.get('peak_time_short')}.", analyst_o.get("status", "Complete")),
        ("02", "Risk Assessor", f"Applied fixed thresholds; classified baseline as {assessor_o.get('risk_level', full_risk)}. Baseline: {assessor_o.get('baseline_recommendation')}.", assessor_o.get("status", "Complete")),
        ("03", "Planning Coordinator", f"Coordinated with {coord_o.get('selected_preference', preference).lower()} style and feedback adjustment ({coord_o.get('feedback_adjustment', 0)}).", coord_o.get("status", "Complete")),
    ]
    for r_num, r_title, r_desc, r_stat in roles_info:
        st.markdown(
            f"""
<div class="trace-step">
    <div class="trace-num" style="background:rgba(233,191,114,0.18); color:#E9BF72">{r_num}</div>
    <div>
        <div class="trace-title">{esc(r_title)}</div>
        <div class="trace-desc">{esc(r_desc)}</div>
        <div style="color:#70C8A0; font-size:0.78rem; font-weight:750; margin-top:4px;">✓ {esc(r_stat)}</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with st.expander("Inspect Raw Role Outputs (JSON for Viva)", expanded=False):
        st.json({
            "forecast_analyst": analyst_o,
            "risk_assessor": assessor_o,
            "planning_coordinator": coord_o,
            "activity_analysis": act_analysis,
            "plan_comparison": comp_data,
        })

# ==================== 6. MEMORY & HISTORY ====================
with tab_memory:
    st.markdown('<div class="hero-eyebrow">Feedback-Aware Memory & Persistence</div>', unsafe_allow_html=True)
    st.caption("Transparent 1-step rule-based adjustment without changing baseline risk thresholds. Synchronized with SQLite persistent storage.")

    fb_col1, fb_col2, fb_col3 = st.columns(3)
    if fb_col1.button("↑ More cautious", use_container_width=True):
        st.session_state.feedback_adjustment = 1
        memory.save_user_preference(st.session_state.user_preference, 1)
        memory.save_feedback_event("More cautious", loc_name)
        st.session_state.feedback_message = "Saved: Recommendations will lean one step more cautious."
        st.rerun()

    if fb_col2.button("✓ Keep selected style", use_container_width=True):
        st.session_state.feedback_adjustment = 0
        memory.save_user_preference(st.session_state.user_preference, 0)
        memory.save_feedback_event("Keep selected style", loc_name)
        st.session_state.feedback_message = "Saved: Recommendations will use standard selected style."
        st.rerun()

    if fb_col3.button("↓ Less cautious", use_container_width=True):
        st.session_state.feedback_adjustment = -1
        memory.save_user_preference(st.session_state.user_preference, -1)
        memory.save_feedback_event("Less cautious", loc_name)
        st.session_state.feedback_message = "Saved: Recommendations will lean one step more relaxed."
        st.rerun()

    if st.session_state.feedback_message:
        st.success(st.session_state.feedback_message)

    st.markdown(
        f"""
<div class="insight-note">
    <strong>Effective Advice Style:</strong> {esc(result.get("effective_preference", preference))}.
    <strong>Baseline Risk Thresholds:</strong> Preserved (LOW &lt;30%, MODERATE 30%–&lt;60%, HIGH ≥60%).
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### SQLite Persistent Activity History")
    sql_records = memory.get_activity_history(limit=15)
    if sql_records:
        sql_df = pd.DataFrame(sql_records)
        st.dataframe(
            sql_df[["location", "activity_type", "rain_probability", "risk_level", "checked_at", "recommendation"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No persistent records saved yet.")

    st.markdown("### Current Session History")
    history = list(reversed(st.session_state.weather_history))
    if history:
        hist_df = pd.DataFrame([
            {
                "Location": x["location"],
                "Activity": x.get("activity", "General"),
                "Window": x.get("time_window", "Full day"),
                "Rain probability": f"{x['rain_probability']:.0%}",
                "Risk": x["risk_level"],
                "Checked at": x["checked_at"],
                "Source": "Sample" if x["demo"] else "Live",
            }
            for x in history
        ])
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.caption("Session history is empty.")

    if st.button("Clear All Memory (Session & SQLite)", type="secondary"):
        st.session_state.weather_history = []
        st.session_state.feedback_adjustment = 0
        memory.clear_memory()
        st.success("All persistent and session memory cleared.")
        st.rerun()

# ---------- Footer ----------
st.markdown(
    """
<div style="text-align:center; padding-top:28px; color:#9BAEC6; font-size:0.78rem;">
    Umbrella 2.0 · Agentic AI System for Context-Aware Weather Planning · Academic Jury Demonstration · Streamlit + LangGraph
</div>
""",
    unsafe_allow_html=True,
)
