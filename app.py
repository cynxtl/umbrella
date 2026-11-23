"""Umbrella 2.0: Deep-Black, Monochromatic, Conversation-First Weather Planning Assistant.

Minimal AI assistant design:
- Pure black canvas (#000000), deep slate (#0D0D0D), white accents (#FFFFFF), muted text (#A3A3A3, #737373)
- Understated header: ☂ umbrella. (zero oversized SVG banners)
- Conversational-first landing: centered greeting, prompt chips, native chat interface
- Context-aware follow-up engine:
  - "I have college tomorrow from 9 to 4. Should I carry an umbrella?"
  - "What if I leave at 5?"
  - "Find me a better time."
- Compact inline recommendation cards, side-by-side plan comparisons, expandable analytics
- Preserved LangGraph Planning Orchestrator, 3 roles, SQLite persistent memory, and offline demo
"""
from __future__ import annotations

import os
import re
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
ENV_VARS = dotenv_values(ROOT / ".env")

st.set_page_config(
    page_title="umbrella.",
    page_icon="☂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Monochromatic, Deep-Black Glassmorphic Styles ----------
st.markdown(
    """
<style>
/* Base Theme */
:root {
    --bg-main: #000000;
    --bg-surface: #0D0D0D;
    --glass-bg: rgba(255, 255, 255, 0.035);
    --glass-border: rgba(255, 255, 255, 0.10);
    --text-primary: #FFFFFF;
    --text-secondary: #A3A3A3;
    --text-muted: #737373;
    --accent-low: #70C8A0;
    --accent-mod: #E9BF72;
    --accent-high: #E88C8C;
}

.stApp {
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
}

[data-testid="stHeader"] {
    background: rgba(0, 0, 0, 0.85) !important;
    backdrop-filter: blur(12px) !important;
}

.block-container {
    max-width: 920px;
    padding-top: 1.5rem;
    padding-bottom: 5.5rem;
}

[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--glass-border) !important;
}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
    color: var(--text-primary) !important;
}

/* Minimal Header */
.top-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0 20px 0;
    border-bottom: 1px solid var(--glass-border);
    margin-bottom: 24px;
}
.brand-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 8px;
}
.brand-title span {
    color: var(--text-muted);
    font-weight: 400;
    font-size: 0.82rem;
    margin-left: 6px;
}

/* Landing Greeting */
.landing-hero {
    text-align: center;
    padding: 48px 16px 32px 16px;
}
.landing-hero h1 {
    font-size: clamp(2rem, 4vw, 2.85rem);
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.04em;
    margin: 0 0 10px 0;
}
.landing-hero p {
    font-size: 1.05rem;
    color: var(--text-secondary);
    margin: 0;
}

/* Chips Container */
.chips-container {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 24px;
    margin-bottom: 30px;
}

/* Inline Glass Cards */
.inline-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 14px;
    padding: 16px 18px;
    margin: 12px 0;
}

.rec-title {
    font-size: 1.15rem;
    font-weight: 750;
    color: var(--text-primary);
    margin-bottom: 4px;
    letter-spacing: -0.02em;
}

.rec-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 10px;
}

/* Semantic Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-low {
    color: var(--accent-low);
    background: rgba(112, 200, 160, 0.12);
    border: 1px solid rgba(112, 200, 160, 0.25);
}
.badge-moderate {
    color: var(--accent-mod);
    background: rgba(233, 191, 114, 0.12);
    border: 1px solid rgba(233, 191, 114, 0.25);
}
.badge-high {
    color: var(--accent-high);
    background: rgba(232, 140, 140, 0.12);
    border: 1px solid rgba(232, 140, 140, 0.25);
}
.badge-mono {
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--glass-border);
}

/* Adaptive Comparison Inline Grid */
.plan-comp-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 10px 0;
}
.comp-box {
    background: rgba(255, 255, 255, 0.025);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 12px 14px;
}
.comp-box.better {
    border-color: rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.05);
}
.comp-box-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 4px;
}
.comp-box-time {
    font-size: 1.05rem;
    font-weight: 750;
    color: var(--text-primary);
    margin-bottom: 2px;
}
.comp-box-pop {
    font-size: 1.35rem;
    font-weight: 850;
    color: var(--text-primary);
}

/* Button & Form Elements */
.stButton > button {
    background: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    border: none !important;
    transition: opacity 0.15s ease;
}
.stButton > button:hover {
    opacity: 0.88;
}

/* Chat Input Styling */
[data-testid="stChatInput"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 4px 8px !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text-primary) !important;
    background: transparent !important;
}

[data-testid="stExpander"] {
    background: transparent !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    margin: 6px 0 !important;
}

/* Trace Step Details */
.trace-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.82rem;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.trace-row:last-child { border-bottom: none; }

footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- State Initialization & Sync ----------
stored_pref, stored_adj = memory.load_user_preference()

for key, default in {
    "messages": [],
    "user_preference": stored_pref,
    "feedback_adjustment": stored_adj,
    "current_plan": {
        "location": "Pune",
        "activity_type": "General",
        "start_time": "09:00",
        "end_time": "17:00",
        "flexibility_hours": 3,
    },
    "last_result": None,
    "api_key_owm": ENV_VARS.get("OPENWEATHER_API_KEY", ""),
    "api_key_groq": ENV_VARS.get("GROQ_API_KEY", ""),
    "demo_mode": True,
    "demo_scenario": "Moderate",
    "unit": "°C",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------- Natural Language Intent & Parameter Parser ----------
def parse_time_token(t_str: str, default_is_pm: bool = False) -> str | None:
    t_str = t_str.strip().lower()
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", t_str)
    if not m:
        return None
    h = int(m.group(1))
    mins = int(m.group(2) or 0)
    period = m.group(3)
    if period == "pm" and h < 12:
        h += 12
    elif period == "am" and h == 12:
        h = 0
    elif period is None:
        if default_is_pm and h < 12:
            h += 12
        elif not default_is_pm and h < 7:
            h += 12  # e.g. 4 -> 16:00
    return f"{h:02d}:{mins:02d}"


def parse_user_query(query: str, ctx: dict) -> tuple[dict, str]:
    """Parse user query into updated plan context and user intent."""
    q = query.strip().lower()
    new_ctx = dict(ctx)
    intent = "plan"

    # 1. Reset / Clear
    if re.search(r"\b(reset|clear|restart|start over)\b", q):
        return new_ctx, "reset"

    # 2. Evidence / Why
    if re.search(r"\b(why|why this|evidence|reason|how did|trace|steps)\b", q):
        return new_ctx, "why"

    # 3. Analytics / Chart
    if re.search(r"\b(chart|graph|timeline|analytics|curve|temperature)\b", q):
        return new_ctx, "analytics"

    # 4. Adaptive comparison / Better time
    if re.search(r"\b(better time|alternative|compare|reschedule|avoid rain|shift|earlier|later|flexib)\b", q):
        intent = "compare"
        new_ctx["flexibility_hours"] = max(2, new_ctx.get("flexibility_hours", 3))

    # 5. Extract Location
    loc_match = re.search(r"\b(?:in|for|at)\s+([a-zA-Z\s]+?)(?:\s+tomorrow|\s+from|\s+between|\?|\.|$)", query, re.IGNORECASE)
    if loc_match:
        loc = loc_match.group(1).strip()
        if len(loc) > 2 and loc.lower() not in {"college", "office", "walk", "home", "work"}:
            new_ctx["location"] = loc.title()

    # 6. Extract Activity
    if re.search(r"\b(college|class|lecture|campus|university)\b", q):
        new_ctx["activity_type"] = "College"
    elif re.search(r"\b(office|work|commute|job)\b", q):
        new_ctx["activity_type"] = "Office commute"
    elif re.search(r"\b(walk|jog|run|stroll)\b", q):
        new_ctx["activity_type"] = "Walking"
    elif re.search(r"\b(outdoor|event|game|match|picnic|party)\b", q):
        new_ctx["activity_type"] = "Outdoor event"
    elif re.search(r"\b(travel|flight|drive|trip)\b", q):
        new_ctx["activity_type"] = "Travel"

    # 7. Extract Time Window
    # Range: e.g. "from 9 to 4", "9am to 4pm", "9 to 16", "between 2 and 6"
    range_match = re.search(
        r"(?:from\s+|between\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|and)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        q,
    )
    if range_match:
        t1_raw = range_match.group(1)
        t2_raw = range_match.group(2)
        # If t2 looks like afternoon/evening without am/pm and is smaller than t1 (e.g. 9 to 4)
        t1 = parse_time_token(t1_raw, default_is_pm=False)
        t2 = parse_time_token(t2_raw, default_is_pm=True)
        if t1 and t2:
            new_ctx["start_time"] = t1
            new_ctx["end_time"] = t2
    else:
        # Follow-up single time: "what if I leave at 5", "stay until 4", "leave at 17:00"
        leave_match = re.search(r"(?:leave\s+at|leave\s+by|until|till|stay\s+until|end\s+at)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", q)
        if leave_match:
            end_t = parse_time_token(leave_match.group(1), default_is_pm=True)
            if end_t:
                new_ctx["end_time"] = end_t
                intent = "plan"
        else:
            # Single event time: "around 5 pm", "at 4", "at 6pm"
            single_match = re.search(r"(?:around|at|by)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", q)
            if single_match and intent != "compare":
                st_t = parse_time_token(single_match.group(1), default_is_pm=True)
                if st_t:
                    new_ctx["start_time"] = st_t
                    # default 2h activity
                    sh = int(st_t.split(":")[0])
                    new_ctx["end_time"] = f"{(sh + 2) % 24:02d}:00"
                    intent = "plan"

    return new_ctx, intent


def get_risk_badge_html(risk: str, pop: float | None = None) -> str:
    r = str(risk).upper()
    css = {"LOW": "badge-low", "MODERATE": "badge-moderate", "HIGH": "badge-high"}.get(r, "badge-moderate")
    text = f"{r} RISK" if pop is None else f"{r} RISK · {pop:.0%}"
    return f'<span class="badge {css}">{text}</span>'


def esc(val) -> str:
    return html.escape(str(val if val is not None else "—"), quote=True)


# ---------- Chart Helper ----------
def render_dark_timeline_chart(timeline: list[dict], unit: str) -> alt.Chart:
    rows = []
    for slot in timeline:
        p = float(slot.get("rain_probability", 0.0))
        t = float(slot.get("temperature", 20.0))
        t_disp = t if unit == "°C" else t * 9 / 5 + 32
        rows.append({
            "Time": str(slot.get("time")),
            "Rain probability (%)": round(p * 100, 1),
            f"Temperature ({unit})": round(t_disp, 1),
            "Conditions": slot.get("description", "Clear"),
        })
    df = pd.DataFrame(rows)
    order = df["Time"].tolist()

    base = alt.Chart(df).encode(
        x=alt.X("Time:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelColor="#A3A3A3", tickSize=0, domain=False)),
        tooltip=[
            alt.Tooltip("Time:N", title="Time"),
            alt.Tooltip("Rain probability (%):Q", title="Rain Risk", format=".1f"),
            alt.Tooltip(f"Temperature ({unit}):Q", title="Temp", format=".1f"),
            alt.Tooltip("Conditions:N", title="Weather"),
        ],
    )
    area = base.mark_area(color="#FFFFFF", opacity=0.08, interpolate="monotone").encode(
        y=alt.Y("Rain probability (%):Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#737373", gridColor="rgba(255,255,255,0.06)", ticks=False, domain=False))
    )
    line = base.mark_line(color="#FFFFFF", strokeWidth=2.2, point=alt.OverlayMarkDef(filled=True, fill="#000000", stroke="#FFFFFF", strokeWidth=2, size=55), interpolate="monotone").encode(
        y="Rain probability (%):Q"
    )
    mod_rule = alt.Chart(pd.DataFrame({"y": [LOW_THRESHOLD * 100]})).mark_rule(color="#E9BF72", strokeDash=[4, 4], strokeWidth=1.2).encode(y="y:Q")
    high_rule = alt.Chart(pd.DataFrame({"y": [HIGH_THRESHOLD * 100]})).mark_rule(color="#E88C8C", strokeDash=[3, 3], strokeWidth=1.2).encode(y="y:Q")

    return (area + line + mod_rule + high_rule).properties(height=200, background="transparent").configure_view(stroke=None)


# ---------- Sidebar Configuration ----------
with st.sidebar:
    st.markdown("### Settings")
    st.session_state.demo_mode = st.toggle("Offline jury demo", value=st.session_state.demo_mode)
    if st.session_state.demo_mode:
        st.session_state.demo_scenario = st.selectbox("Demo scenario", ["Moderate", "Low", "High"], index=["Moderate", "Low", "High"].index(st.session_state.demo_scenario))
    else:
        st.session_state.api_key_owm = st.text_input("OpenWeather API Key", value=st.session_state.api_key_owm, type="password")

    st.session_state.api_key_groq = st.text_input("Groq API Key (optional)", value=st.session_state.api_key_groq, type="password")
    st.session_state.unit = st.radio("Unit", ["°C", "°F"], horizontal=True)

    st.divider()
    st.markdown("### Personalization")
    st.session_state.user_preference = st.selectbox(
        "Advice Style",
        ["Conservative", "Balanced", "Relaxed"],
        index=["Conservative", "Balanced", "Relaxed"].index(st.session_state.user_preference),
    )

    st.markdown("**Session & SQLite Memory**")
    m_col1, m_col2 = st.columns(2)
    if m_col1.button("↑ Cautious", use_container_width=True):
        st.session_state.feedback_adjustment = 1
        memory.save_user_preference(st.session_state.user_preference, 1)
        st.toast("Saved: leaning more cautious")
    if m_col2.button("↓ Relaxed", use_container_width=True):
        st.session_state.feedback_adjustment = -1
        memory.save_user_preference(st.session_state.user_preference, -1)
        st.toast("Saved: leaning more relaxed")

    if st.button("Reset Conversation", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()


# ---------- Slim Header ----------
st.markdown(
    """
<div class="top-nav">
    <div class="brand-title">
        ☂ umbrella. <span>planning intelligence</span>
    </div>
    <div>
        <span class="badge badge-mono">agentic ai</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------- Execute Agent Workflow Helper ----------
def execute_agent_for_plan(plan_ctx: dict) -> dict:
    return run_agent(
        location=plan_ctx["location"],
        activity_type=plan_ctx["activity_type"],
        start_time=plan_ctx["start_time"],
        end_time=plan_ctx["end_time"],
        flexibility_hours=plan_ctx.get("flexibility_hours", 3),
        preference=st.session_state.user_preference,
        caution_adjustment=int(st.session_state.feedback_adjustment),
        api_key_owm=st.session_state.api_key_owm,
        api_key_groq=st.session_state.api_key_groq,
        demo_mode=st.session_state.demo_mode,
        demo_scenario=st.session_state.demo_scenario,
    )


# ---------- Render Message Helper ----------
def render_assistant_response(data: dict):
    explanation = data.get("explanation", "")
    act_analysis = data.get("activity_analysis") or {}
    comp = data.get("plan_comparison") or {}
    timeline = data.get("forecast_timeline") or []
    trace = data.get("execution_trace") or []
    unit = st.session_state.unit

    rec = data.get("personalized_recommendation", data.get("recommendation", "Plan prepared"))
    act_pop = float(act_analysis.get("peak_pop", data.get("rain_probability", 0.0)))
    act_risk = str(act_analysis.get("risk_level", data.get("risk_level", "LOW")))
    temp = float(act_analysis.get("temp_max", data.get("temperature", 20.0)))
    temp_disp = temp if unit == "°C" else temp * 9 / 5 + 32
    conds = act_analysis.get("conditions", data.get("description", "Clear"))
    time_lbl = f"{data.get('start_time', '09:00')} – {data.get('end_time', '17:00')}"

    # Natural response text
    st.write(explanation)

    # Inline Glass Card
    st.markdown(
        f"""
<div class="inline-card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <div class="rec-title">{esc(rec)}</div>
            <div class="rec-meta">
                <span>📍 {esc(data.get('location', 'Pune'))}</span>
                <span>·</span>
                <span>🎯 {esc(data.get('activity_type', 'General'))} ({esc(time_lbl)})</span>
                <span>·</span>
                <span>🌤️ {esc(conds)} · {temp_disp:.1f}{unit}</span>
            </div>
        </div>
        <div>
            {get_risk_badge_html(act_risk, act_pop)}
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # If Plan Comparison has better alternative or was specifically requested
    if data.get("_show_comparison") or comp.get("has_better_alternative"):
        orig_p = comp.get("original_plan") or {}
        rec_p = comp.get("recommended_plan") or orig_p
        has_better = bool(comp.get("has_better_alternative"))
        reduction = float(comp.get("risk_reduction_pp", 0.0))

        st.markdown(
            f"""
<div class="inline-card" style="border-color:rgba(255,255,255,0.18);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-size:0.8rem; font-weight:700; text-transform:uppercase; color:var(--text-secondary)">
            {'⚡ Lower-Risk Window Suggested' if has_better else '✓ Original Timing Is Optimal'}
        </span>
        <span class="badge badge-mono">{reduction:.0f} pp risk reduction</span>
    </div>
    <div class="plan-comp-grid">
        <div class="comp-box">
            <div class="comp-box-label">Original Plan</div>
            <div class="comp-box-time">{esc(orig_p.get('label', time_lbl))}</div>
            <div class="comp-box-pop">{orig_p.get('peak_pop', act_pop):.0%} <span style="font-size:0.75rem; color:var(--text-muted)">peak rain</span></div>
        </div>
        <div class="comp-box {'better' if has_better else ''}">
            <div class="comp-box-label">{'Suggested Alternative' if has_better else 'Current Plan'}</div>
            <div class="comp-box-time">{esc(rec_p.get('label', time_lbl))}</div>
            <div class="comp-box-pop">{rec_p.get('peak_pop', act_pop):.0%} <span style="font-size:0.75rem; color:var(--text-muted)">peak rain</span></div>
        </div>
    </div>
    <div style="font-size:0.86rem; color:var(--text-secondary); margin-top:8px;">
        {esc(comp.get('why_this_plan', ''))}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Compact Expanders for Tools
    with st.expander("📊 View Forecast Timeline", expanded=bool(data.get("_show_analytics"))):
        if timeline:
            st.altair_chart(render_dark_timeline_chart(timeline, unit), use_container_width=True)
            st.caption("Forecast-slot rain probabilities across tomorrow. Dashed markers denote 30% and 60% risk thresholds.")

    with st.expander("🔍 View Agent Execution Trace", expanded=bool(data.get("_show_evidence"))):
        if trace:
            for s in trace:
                st.markdown(
                    f"""
<div class="trace-row">
    <div><strong>{s.get('step')}. {esc(s.get('title'))}</strong> <span style="color:#737373">({esc(s.get('tool_or_node'))})</span></div>
    <div><span class="badge badge-mono">{s.get('duration_ms', 0)}ms</span> <span style="color:#70C8A0">✓</span></div>
</div>
""",
                    unsafe_allow_html=True,
                )


# ---------- Main Content Area: Landing or Conversation ----------
if not st.session_state.messages:
    # Minimal Landing Experience
    st.markdown(
        """
<div class="landing-hero">
    <h1>What are you planning?</h1>
    <p>Weather-aware decisions, made simple.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # Suggested prompt chips
    st.markdown('<div class="chips-container">', unsafe_allow_html=True)
    chip_cols = st.columns(4)
    chips = [
        "College tomorrow from 9 to 4",
        "Evening walk around 5 PM",
        "Outdoor event tomorrow afternoon",
        "Office commute tomorrow morning",
    ]
    selected_chip = None
    for idx, (col, text) in enumerate(zip(chip_cols, chips)):
        with col:
            if st.button(text, key=f"chip_{idx}", use_container_width=True):
                selected_chip = text
    st.markdown("</div>", unsafe_allow_html=True)

    if selected_chip:
        st.session_state.messages.append({"role": "user", "content": selected_chip})
        new_plan, intent = parse_user_query(selected_chip, st.session_state.current_plan)
        st.session_state.current_plan = new_plan
        with st.spinner("Evaluating weather…"):
            res = execute_agent_for_plan(new_plan)
            res["_show_comparison"] = intent == "compare"
            st.session_state.last_result = res
            st.session_state.messages.append({"role": "assistant", "data": res})
        st.rerun()

else:
    # Render Conversation History
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                render_assistant_response(msg["data"])


# ---------- Chat Input Handler ----------
user_prompt = st.chat_input("Ask umbrella anything about your plans...")

if user_prompt:
    # 1. Append user prompt
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Parse intent & update context
    new_plan, intent = parse_user_query(user_prompt, st.session_state.current_plan)
    st.session_state.current_plan = new_plan

    # 3. Handle special intents or standard plan
    if intent == "reset":
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()
    elif intent == "why" and st.session_state.last_result:
        res = dict(st.session_state.last_result)
        res["_show_evidence"] = True
        res["explanation"] = f"Here is the decision evidence: The peak rain probability is {res.get('activity_analysis', {}).get('peak_pop', 0):.0%}, classifying your {res.get('activity_type')} as {res.get('risk_level')} risk."
        st.session_state.messages.append({"role": "assistant", "data": res})
        st.rerun()
    elif intent == "analytics" and st.session_state.last_result:
        res = dict(st.session_state.last_result)
        res["_show_analytics"] = True
        res["explanation"] = f"Here is the forecast distribution and temperature curve for tomorrow in {res.get('location')}."
        st.session_state.messages.append({"role": "assistant", "data": res})
        st.rerun()
    else:
        # Execute workflow
        with st.spinner("Evaluating weather…"):
            res = execute_agent_for_plan(new_plan)
            res["_show_comparison"] = (intent == "compare")
            st.session_state.last_result = res
            st.session_state.messages.append({"role": "assistant", "data": res})
        st.rerun()
