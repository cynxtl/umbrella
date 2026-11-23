"""Streamlit-only light dashboard for the Weather Planning Agent Jury 2 demo."""
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
from dotenv import load_dotenv

from agent import (
    run_agent,
    build_demo_result,
    coordinate_recommendation,
    LOW_THRESHOLD,
    HIGH_THRESHOLD,
)

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
st.set_page_config(
    page_title="Weather Planning Agent",
    page_icon="☂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system: clean light surfaces, restrained red accents ----------
st.markdown(
    """
<style>
:root { color-scheme: light; }
.stApp { background: #f5f7fb; color: #172033; }
[data-testid="stHeader"] { background: rgba(245,247,251,.92); }
.block-container { max-width: 1500px; padding-top: 4.5rem; padding-bottom: 2.6rem; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e9f1; }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
[data-testid="stSidebar"] h3 { color: #172033; font-size: 1rem; letter-spacing: -.015em; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #657087; }
[data-testid="stSidebar"] hr { border-color: #edf0f5; }

.hero { display:flex; align-items:center; gap:18px; padding:22px 26px; margin:0 0 18px 0; border:1px solid #e7eaf1; border-radius:22px; background:linear-gradient(112deg,#ffffff 0%,#fff 57%,#fff2f2 100%); box-shadow:0 8px 26px rgba(30,41,59,.045); }
.hero img { width:76px; height:76px; object-fit:contain; flex-shrink:0; }
.hero h1 { font-size:clamp(1.65rem,3vw,2.45rem); margin:0; letter-spacing:-.045em; line-height:1.08; color:#172033; font-weight:850; }
.hero h1 span { color:#c62832; }
.hero p { margin:7px 0 0; color:#657087; font-size:.98rem; }
.eyebrow { color:#bf2630; font-size:.70rem; text-transform:uppercase; letter-spacing:.15em; font-weight:850; margin-bottom:7px; }

.section-heading { display:flex; align-items:center; gap:10px; margin:10px 0 4px; color:#182238; font-size:1.22rem; font-weight:800; letter-spacing:-.025em; }
.section-subtitle { color:#758097; margin:0 0 14px; font-size:.88rem; }
.location-strip { display:flex; align-items:center; gap:9px; flex-wrap:wrap; margin-bottom:14px; }
.location-name { color:#172033; font-size:1.18rem; font-weight:850; letter-spacing:-.02em; }
.pill { display:inline-block; border-radius:999px; padding:5px 10px; font-weight:800; letter-spacing:.035em; font-size:.72rem; }
.pill-live { color:#176847; background:#e9f8f0; border:1px solid #c6ecd8; }
.pill-demo { color:#8a5200; background:#fff4dd; border:1px solid #f3dfb1; }
.pill-low { color:#176847; background:#e7f7ef; border:1px solid #bfe8d1; }
.pill-moderate { color:#8a5a00; background:#fff5d9; border:1px solid #f0dfa6; }
.pill-high { color:#a5222b; background:#fff0f0; border:1px solid #f7c8cb; }

.surface { border:1px solid #e5e9f1; background:#ffffff; border-radius:18px; padding:19px 21px; height:100%; box-shadow:0 5px 18px rgba(30,41,59,.035); }
[data-testid="stVerticalBlockBorderWrapper"] { background:#ffffff; border:1px solid #e5e9f1; border-radius:18px; padding:18px 20px; box-shadow:0 5px 18px rgba(30,41,59,.035); }
[data-testid="stVerticalBlockBorderWrapper"] h3 { margin-top:0; color:#182238; letter-spacing:-.02em; }
[data-testid="stVerticalBlockBorderWrapper"] p { color:#4e5b72; }
.recommendation { border:1px solid #bfe8d1; background:linear-gradient(120deg,#edfbf4 0%,#f8fffb 100%); border-radius:15px; padding:20px; }
.recommendation .big { font-size:clamp(1.25rem,2vw,1.8rem); font-weight:850; line-height:1.18; letter-spacing:-.03em; color:#135e43; }
.recommendation .support { color:#547565; font-size:.89rem; margin-top:8px; line-height:1.5; }
.baseline-panel { margin-top:14px; padding:14px 16px; border:1px solid #e6eaf2; border-radius:14px; background:#f8fafc; }
.baseline-row { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:7px; }
.baseline-text { margin:0; color:#25324a; font-size:1rem; font-weight:750; line-height:1.35; }
.muted { color:#748097; font-size:.84rem; }
.risk-low { color:#176847; background:#e7f7ef; border:1px solid #bfe8d1; }
.risk-moderate { color:#8a5a00; background:#fff5d9; border:1px solid #f0dfa6; }
.risk-high { color:#a5222b; background:#fff0f0; border:1px solid #f7c8cb; }

div[data-testid="stMetric"] { background:#ffffff; border:1px solid #e5e9f1; border-radius:15px; padding:15px 17px; box-shadow:0 4px 14px rgba(30,41,59,.025); }
div[data-testid="stMetricLabel"] { color:#6e7990; font-size:.8rem; }
div[data-testid="stMetricValue"] { color:#172033; font-weight:850; letter-spacing:-.035em; }
div[data-testid="stMetricDelta"] { font-size:.76rem; }
[data-testid="stForm"] { max-width:900px; margin:0 auto 1.25rem; background:#ffffff; padding:14px 18px 8px; border:1px solid #e5e9f1; border-radius:16px; box-shadow:0 4px 14px rgba(30,41,59,.03); }
.stTextInput input, .stSelectbox [data-baseweb="select"], .stRadio, .stTextArea textarea { border-radius:10px; }
.stButton > button, .stFormSubmitButton > button { border-radius:11px; font-weight:750; border:1px solid #dce2eb; transition:all .15s ease; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:#c62832; color:#ffffff; border:1px solid #c62832; }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover { background:#a91f28; border-color:#a91f28; color:#fff; }
.stButton > button:hover { border-color:#c62832; color:#a91f28; }
[data-testid="stTabs"] button[role="tab"] { font-weight:750; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:#b8202b; }
[data-testid="stProgressBar"] > div > div { background:#c62832; }
div[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stExpander"] { background:#fff; border:1px solid #e5e9f1; border-radius:13px; }
[data-testid="stDataFrame"] { border:1px solid #e5e9f1; border-radius:12px; overflow:hidden; }
hr { border-color:#e7ebf2; }
footer { visibility:hidden; }
.small-kicker { color:#7a8498; font-size:.72rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em; }
.insight { border-radius:13px; padding:13px 15px; background:#f8fafc; border:1px solid #e6eaf2; margin:7px 0; color:#334057; line-height:1.5; }
.insight strong { color:#172033; }
.role-card { display:flex; align-items:flex-start; gap:14px; padding:16px; margin:9px 0; background:#fff; border:1px solid #e5e9f1; border-radius:15px; box-shadow:0 4px 12px rgba(30,41,59,.025); }
.role-number { display:flex; align-items:center; justify-content:center; flex-shrink:0; width:38px; height:38px; border-radius:12px; background:#fff0f0; color:#b8202b; font-size:.86rem; font-weight:900; }
.role-title { font-size:.98rem; font-weight:850; color:#1c2840; margin:0 0 4px; }
.role-description { color:#637087; font-size:.88rem; line-height:1.5; }
.role-status { color:#18734d; font-size:.77rem; font-weight:800; margin-top:7px; }
.footer-note { color:#8a94a7; font-size:.78rem; text-align:center; padding-top:15px; }
@media (max-width: 800px) { .hero { padding:16px; gap:12px; } .hero img { width:56px; height:56px; } .surface { padding:15px; } [data-testid="stVerticalBlockBorderWrapper"] { padding:14px; } }
</style>
""",
    unsafe_allow_html=True,
)

# Session state is intentionally short-term memory, not persistent storage.
for key, default in {
    "weather_history": [],
    "last_result": None,
    "feedback_adjustment": 0,
    "feedback_events": [],
    "last_location": "Pune",
    "feedback_message": "",
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


def rain_probability_chart(frame: pd.DataFrame) -> alt.Chart:
    order = frame["Time"].tolist()
    base = alt.Chart(frame).encode(
        x=alt.X("Time:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelColor="#68748a", tickSize=0, domain=False)),
        tooltip=[
            alt.Tooltip("Time:N", title="Forecast time"),
            alt.Tooltip("Rain probability (%):Q", title="Rain probability", format=".1f"),
            alt.Tooltip("Risk band:N", title="Risk band"),
            alt.Tooltip("Conditions:N", title="Conditions"),
        ],
    )
    area = base.mark_area(color="#e45a62", opacity=0.13, interpolate="monotone").encode(
        y=alt.Y("Rain probability (%):Q", title="Chance of rain", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#68748a", gridColor="#edf0f5", titleColor="#68748a", ticks=False, domain=False))
    )
    line = base.mark_line(color="#c62832", strokeWidth=3, point=alt.OverlayMarkDef(filled=True, fill="#ffffff", stroke="#c62832", strokeWidth=2, size=75), interpolate="monotone").encode(
        y="Rain probability (%):Q"
    )
    moderate = alt.Chart(pd.DataFrame({"threshold": [LOW_THRESHOLD * 100]})).mark_rule(color="#d18a18", strokeDash=[6, 4], strokeWidth=1.5).encode(y="threshold:Q")
    high = alt.Chart(pd.DataFrame({"threshold": [HIGH_THRESHOLD * 100]})).mark_rule(color="#a5222b", strokeDash=[3, 4], strokeWidth=1.5).encode(y="threshold:Q")
    return (area + line + moderate + high).properties(height=300, background="#ffffff").configure_view(stroke=None).configure_axis(labelFont="sans-serif", titleFont="sans-serif", labelFontSize=11, titleFontSize=11).configure_legend(labelColor="#68748a")


def temperature_chart(frame: pd.DataFrame, unit: str) -> alt.Chart:
    order = frame["Time"].tolist()
    temp_column = f"Temperature ({unit})"
    return alt.Chart(frame).mark_line(color="#3478c8", strokeWidth=2.8, point=alt.OverlayMarkDef(filled=True, fill="#ffffff", stroke="#3478c8", strokeWidth=2, size=65), interpolate="monotone").encode(
        x=alt.X("Time:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelColor="#68748a", tickSize=0, domain=False)),
        y=alt.Y(f"{temp_column}:Q", title=f"Temperature ({unit})", axis=alt.Axis(labelColor="#68748a", titleColor="#68748a", gridColor="#edf0f5", domain=False, ticks=False)),
        tooltip=[alt.Tooltip("Time:N", title="Forecast time"), alt.Tooltip(f"{temp_column}:Q", title="Temperature", format=".1f"), alt.Tooltip("Conditions:N", title="Conditions")],
    ).properties(height=260, background="#ffffff").configure_view(stroke=None).configure_axis(labelFont="sans-serif", titleFont="sans-serif", labelFontSize=11, titleFontSize=11)


def risk_distribution_chart(frame: pd.DataFrame) -> alt.Chart:
    levels = ["LOW", "MODERATE", "HIGH"]
    counts = frame["Risk band"].value_counts().reindex(levels, fill_value=0).rename_axis("Risk band").reset_index(name="Forecast slots")
    return alt.Chart(counts).mark_bar(cornerRadiusEnd=6, size=28).encode(
        y=alt.Y("Risk band:N", sort=levels, title=None, axis=alt.Axis(labelColor="#68748a", domain=False, ticks=False)),
        x=alt.X("Forecast slots:Q", title="Number of 3-hour forecast slots", axis=alt.Axis(labelColor="#68748a", titleColor="#68748a", gridColor="#edf0f5", ticks=False, domain=False)),
        color=alt.Color("Risk band:N", scale=alt.Scale(domain=levels, range=["#23966b", "#e3a126", "#c62832"]), legend=None),
        tooltip=["Risk band:N", "Forecast slots:Q"],
    ).properties(height=160, background="#ffffff").configure_view(stroke=None).configure_axis(labelFont="sans-serif", titleFont="sans-serif", labelFontSize=11, titleFontSize=11)


def append_history(result: dict, location: str, demo: bool):
    check_id = uuid.uuid4().hex[:10]
    result["_check_id"] = check_id
    entry = {
        "check_id": check_id,
        "location": location.strip(),
        "rain_probability": float(result.get("rain_probability", 0.0)),
        "risk_level": result.get("risk_level", "—"),
        "peak_time": result.get("peak_time_short", "—"),
        "checked_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "demo": bool(demo),
    }
    st.session_state.weather_history.append(entry)
    st.session_state.weather_history = st.session_state.weather_history[-25:]


# Header logo is a cropped derivative of the supplied, fully editable SVG.
logo_path = ROOT / "umbrella_mark.svg"
if not logo_path.exists():
    logo_path = ROOT / "umbrella_logo.svg"
try:
    svg_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    logo_html = f'<img src="data:image/svg+xml;base64,{svg_b64}" alt="Umbrella emblem" />'
except OSError:
    logo_html = '<div style="font-size:3rem">☂️</div>'

st.markdown(
    f'''<div class="hero">{logo_html}<div><div class="eyebrow">Plan smarter · Stay prepared</div><h1>Weather Planning <span>Agent</span></h1><p>Forecast analytics, explainable decisions and personalized planning.</p></div></div>''',
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Planning workspace")
    st.caption("Choose a location, advice style and forecast source.")
    owm_key = st.text_input("OpenWeather API key", value=os.environ.get("OPENWEATHER_API_KEY", ""), type="password", help="Required for live forecast data.")
    groq_key = st.text_input("Groq API key · optional", value=os.environ.get("GROQ_API_KEY", ""), type="password", help="Only used to turn forecast facts into a short natural-language explanation.")
    if owm_key.strip():
        os.environ["OPENWEATHER_API_KEY"] = owm_key.strip()
    if groq_key.strip():
        os.environ["GROQ_API_KEY"] = groq_key.strip()

    st.divider()
    st.markdown("### Personalization")
    unit = st.radio("Temperature unit", ["°C", "°F"], horizontal=True, key="temperature_unit")
    preference = st.selectbox(
        "Advice style", ["Conservative", "Balanced", "Relaxed"], index=1,
        help="Changes personalized advice, not the baseline risk level.",
    )
    adjustment = int(st.session_state.feedback_adjustment)
    if adjustment > 0:
        st.caption("Session memory · leaning more cautious")
    elif adjustment < 0:
        st.caption("Session memory · leaning more relaxed")
    else:
        st.caption("Session memory · using your selected style")

    st.divider()
    demo_mode = st.toggle("Offline jury demo", value=True, help="Uses clearly labelled sample data; no weather API request is made.")
    if demo_mode:
        demo_scenario = st.selectbox("Sample scenario", ["Moderate", "Low", "High"], index=0)
        st.caption("Sample data · not a live forecast")
    else:
        demo_scenario = "Moderate"
        st.caption("Live weather needs a valid OpenWeather key and an internet connection.")

    st.divider()
    with st.expander("Baseline risk rules", expanded=False):
        st.markdown(f"- **LOW:** below {LOW_THRESHOLD:.0%}\n- **MODERATE:** {LOW_THRESHOLD:.0%}–less than {HIGH_THRESHOLD:.0%}\n- **HIGH:** {HIGH_THRESHOLD:.0%} and above")
        st.caption("Python determines the baseline risk. The optional LLM only explains the result.")

# ---------- Location query ----------
with st.form("weather_check", clear_on_submit=False):
    search_col, action_col = st.columns([1, 1], vertical_alignment="bottom", gap="medium")
    with search_col:
        location = st.text_input("Planning location", value=st.session_state.last_location, placeholder="Search a city, e.g. Pune, IN")
    with action_col:
        submitted = st.form_submit_button("Analyze forecast  →", type="primary", use_container_width=True)

if submitted:
    if not location.strip():
        st.warning("Enter a city or location to analyze tomorrow's forecast.")
    elif demo_mode:
        result = build_demo_result(location, demo_scenario, preference, int(st.session_state.feedback_adjustment))
        st.session_state.last_result = result
        st.session_state.last_location = location.strip()
        append_history(result, location.strip(), True)
    elif not os.environ.get("OPENWEATHER_API_KEY"):
        st.error("OpenWeather API key is missing. Add it in the sidebar, or enable Offline jury demo.")
    else:
        with st.spinner("Forecast Analyst is reviewing tomorrow's forecast…"):
            result = run_agent(location, preference=preference, caution_adjustment=int(st.session_state.feedback_adjustment))
        if result.get("error") and result.get("rain_probability") is None:
            st.error(result.get("explanation") or "Couldn't retrieve the forecast. Check the location and try again.")
            with st.expander("Troubleshooting"):
                st.markdown("- Try a city name such as `Pune, IN`.\n- Confirm the OpenWeather key is active.\n- Check your internet connection or enable Offline jury demo.")
        else:
            st.session_state.last_result = result
            st.session_state.last_location = location.strip()
            append_history(result, location.strip(), False)

result = st.session_state.last_result
if result:
    is_demo = bool(result.get("demo_mode"))
    if is_demo:
        st.info("Offline demo is active · all forecast values below are simulated examples, not live weather.", icon="🧪")
    else:
        st.caption(f"Forecast date: {result.get('forecast_date', 'Tomorrow')} · Retrieved with OpenWeather forecast data")

    collab = coordinate_recommendation(result, preference, int(st.session_state.feedback_adjustment))
    probability = max(0.0, min(1.0, float(result.get("rain_probability", 0.0))))
    temp_c = float(result.get("temperature", 0.0))
    temp_display = to_display_temp(temp_c, unit)
    risk = str(result.get("risk_level", risk_for_probability(probability))).upper()
    risk_css = {"LOW": "risk-low", "MODERATE": "risk-moderate", "HIGH": "risk-high"}.get(risk, "risk-moderate")
    risk_class = {"LOW": "LOW", "MODERATE": "MODERATE", "HIGH": "HIGH"}.get(risk, "MODERATE")
    frame = make_timeline(result, unit)
    slot_count = len(frame)
    mean_probability = float(frame["Rain probability (%)"].mean() / 100) if slot_count else probability
    temp_column = f"Temperature ({unit})"
    temp_min = float(frame[temp_column].min()) if slot_count else temp_display
    temp_max = float(frame[temp_column].max()) if slot_count else temp_display
    moderate_slots = int((frame["Rain probability (%)"] >= LOW_THRESHOLD * 100).sum()) if slot_count else int(probability >= LOW_THRESHOLD)
    high_slots = int((frame["Rain probability (%)"] >= HIGH_THRESHOLD * 100).sum()) if slot_count else int(probability >= HIGH_THRESHOLD)
    current_preference = collab["coordinator_output"]["selected_preference"]

    # Context line
    loc_col, status_col = st.columns([3, 1])
    with loc_col:
        st.markdown(f'<div class="location-strip"><span class="location-name">📍 {esc(result.get("location", st.session_state.last_location))}</span><span class="pill {risk_css}">{esc(risk)} RISK</span></div>', unsafe_allow_html=True)
    with status_col:
        st.markdown(f'<div style="text-align:right"><span class="pill {"pill-demo" if is_demo else "pill-live"}">{"SAMPLE DATA" if is_demo else "LIVE FORECAST"}</span></div>', unsafe_allow_html=True)

    # Four compact, high-signal metrics.
    metrics = st.columns(4)
    metrics[0].metric("Peak rain probability", f"{probability:.0%}", help="Highest rain probability among tomorrow's available forecast slots.")
    metrics[1].metric("Peak rain time", result.get("peak_time_short", "—"))
    metrics[2].metric("Average slot probability", f"{mean_probability:.0%}", help="Arithmetic mean of the forecast-slot rain probabilities; not an all-day cumulative probability.")
    metrics[3].metric("Temperature range", f"{temp_min:.0f}–{temp_max:.0f}{unit}", help="Lowest to highest forecast temperature across the displayed slots.")

    dashboard_tab, analytics_tab, agent_tab, history_tab = st.tabs(["Overview", "Forecast analytics", "Agent & memory", "Session history"])

    # ========================= Overview =========================
    with dashboard_tab:
        left, right = st.columns([1.04, 1.5], gap="large")
        with left:
            with st.container(border=True):
                st.markdown("### ☂️ Recommendation")
                st.markdown(
                    f'<div class="recommendation"><div class="small-kicker">Personalized plan</div><div class="big">{esc(collab["personalized_recommendation"])}</div><div class="support">Based on {current_preference.lower()} advice preferences and the current feedback setting.</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="baseline-panel"><span class="small-kicker">Baseline decision · unchanged</span><div class="baseline-row"><p class="baseline-text">{esc(result.get("recommendation", "—"))}</p><span class="pill {risk_css}">{esc(risk)} RISK</span></div></div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("### Conditions at the peak period")
                st.markdown(f'<div style="font-size:1.65rem;font-weight:850;color:#1b2940;letter-spacing:-.04em">{temp_display:.1f}{unit}</div><div style="color:#59677e;font-size:.91rem;margin-top:2px">{esc(result.get("description", "Conditions unavailable"))}</div><div class="muted" style="margin-top:8px">{esc(result.get("peak_rain_time", result.get("peak_time_short", "Peak forecast slot")))}</div>', unsafe_allow_html=True)
        with right:
            with st.container(border=True):
                st.markdown("### Tomorrow at a glance")
                st.markdown('<div class="muted">Rain probability by forecast slot. Dashed rules mark the baseline risk thresholds.</div>', unsafe_allow_html=True)
                if slot_count:
                    st.altair_chart(rain_probability_chart(frame), use_container_width=True)
                else:
                    st.info("The provider did not return a forecast timeline for this result.")

        with st.container(border=True):
            st.markdown("### What this forecast tells us")
            if probability >= HIGH_THRESHOLD:
                headline = f"The peak slot reaches {probability:.0%}, crossing the {HIGH_THRESHOLD:.0%} high-risk threshold."
                takeaway = "An umbrella is strongly recommended for the forecast period with the highest rain probability."
            elif probability >= LOW_THRESHOLD:
                headline = f"The peak slot is {probability:.0%}, inside the moderate-risk band."
                takeaway = "The forecast is uncertain enough that carrying an umbrella is a sensible precaution."
            else:
                headline = f"The peak slot is {probability:.0%}, below the {LOW_THRESHOLD:.0%} moderate-risk threshold."
                takeaway = "Rain probability is comparatively low across the highest-risk slot, although forecasts can change."
            st.markdown(f'<div class="insight"><strong>Peak-risk insight</strong><br>{esc(headline)} {esc(takeaway)}</div>', unsafe_allow_html=True)
            if slot_count:
                st.markdown(f'<div class="insight"><strong>Forecast coverage</strong><br>{moderate_slots} of {slot_count} forecast slots reach at least {LOW_THRESHOLD:.0%} rain probability; {high_slots} reach {HIGH_THRESHOLD:.0%} or above.</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="insight"><strong>Temperature range</strong><br>Forecast temperature ranges from {temp_min:.1f}{unit} to {temp_max:.1f}{unit} across the displayed slots.</div>', unsafe_allow_html=True)

        with st.expander("AI explanation", expanded=False):
            st.write(result.get("explanation", "A rule-based summary is not available."))
            if not result.get("llm_available", True) and not is_demo:
                st.caption("The optional language model was unavailable; the deterministic fallback explanation is shown.")

    # ========================= Forecast analytics =========================
    with analytics_tab:
        st.markdown('<div class="section-heading">Forecast analytics</div><div class="section-subtitle">Understand when rain risk peaks, how temperatures move, and how the slots map to your risk bands.</div>', unsafe_allow_html=True)
        chart_left, chart_right = st.columns([1.45, 1], gap="large")
        with chart_left:
            with st.container(border=True):
                st.markdown("### Rain probability curve")
                st.markdown('<div class="muted">Each point is a provider forecast slot, typically spaced three hours apart.</div>', unsafe_allow_html=True)
                if slot_count:
                    st.altair_chart(rain_probability_chart(frame), use_container_width=True)
                    st.caption(f"Moderate starts at {LOW_THRESHOLD:.0%} · High starts at {HIGH_THRESHOLD:.0%}. The main risk decision uses the peak probability.")
                else:
                    st.info("No forecast slots available to chart.")
        with chart_right:
            with st.container(border=True):
                st.markdown("### Forecast risk distribution")
                st.markdown('<div class="muted">Count of slots in each baseline risk band.</div>', unsafe_allow_html=True)
                if slot_count:
                    st.altair_chart(risk_distribution_chart(frame), use_container_width=True)
                st.markdown(f'<div class="insight"><strong>{moderate_slots}/{slot_count if slot_count else 0} slots</strong> are at least moderate risk.</div>', unsafe_allow_html=True)

        temp_left, temp_right = st.columns([1.2, 1], gap="large")
        with temp_left:
            with st.container(border=True):
                st.markdown("### Temperature through the day")
                st.markdown('<div class="muted">Displayed in the selected unit.</div>', unsafe_allow_html=True)
                if slot_count:
                    st.altair_chart(temperature_chart(frame, unit), use_container_width=True)
        with temp_right:
            with st.container(border=True):
                st.markdown("### Forecast-slot detail")
                st.markdown('<div class="muted">Exact values used by the analytics above.</div>', unsafe_allow_html=True)
                if slot_count:
                    visible = frame[["Time", "Rain probability (%)", temp_column, "Risk band", "Conditions"]].copy()
                    visible["Rain probability (%)"] = visible["Rain probability (%)"].map(lambda value: f"{value:.0f}%")
                    visible[temp_column] = visible[temp_column].map(lambda value: f"{value:.1f}°")
                    st.dataframe(visible, use_container_width=True, hide_index=True, height=min(360, 42 + 36 * len(visible)))
                else:
                    st.caption("Forecast detail is unavailable.")
        st.caption("Interpretation note: forecast-slot probabilities are not added together. The average shown above is a simple mean of available slots, not a cumulative all-day probability.")

    # ========================= Agent and feedback memory =========================
    with agent_tab:
        st.markdown('<div class="section-heading">Collaborative agent workflow</div><div class="section-subtitle">Three role-based components pass structured results to each other. The baseline decision stays deterministic.</div>', unsafe_allow_html=True)
        analyst = collab["analyst_output"]
        assessor = collab["assessor_output"]
        coordinator = collab["coordinator_output"]
        roles = [
            ("01", "Forecast Analyst", f"Prepared forecast facts from {analyst.get('slots_reviewed', result.get('forecast_slots', slot_count))} slots, including {probability:.0%} peak rain probability at {result.get('peak_time_short', 'the peak slot')}.", analyst.get("status", "Complete")),
            ("02", "Risk Assessor", f"Applied the fixed thresholds and classified the baseline risk as {assessor.get('risk_level', risk)}. Baseline action: {assessor.get('baseline_recommendation', result.get('recommendation', '—'))}.", assessor.get("status", "Complete")),
            ("03", "Planning Coordinator", f"Combined baseline risk with {coordinator.get('selected_preference', preference).lower()} style and session feedback. Personalized action: {coordinator.get('personalized_recommendation', '—')}.", coordinator.get("status", "Complete")),
        ]
        for number, title, desc, status in roles:
            st.markdown(f'<div class="role-card"><div class="role-number">{number}</div><div><div class="role-title">{esc(title)}</div><div class="role-description">{esc(desc)}</div><div class="role-status">✓ {esc(status)}</div></div></div>', unsafe_allow_html=True)
        with st.expander("Inspect the structured role outputs"):
            st.json({"forecast_analyst": analyst, "risk_assessor": assessor, "planning_coordinator": coordinator})

        st.markdown('<div class="section-heading">Feedback-aware session memory</div><div class="section-subtitle">This changes the advice style for this session; it does not train a model or alter risk thresholds.</div>', unsafe_allow_html=True)
        fb1, fb2, fb3 = st.columns(3)
        if fb1.button("↑ More cautious", use_container_width=True):
            st.session_state.feedback_adjustment = 1
            st.session_state.feedback_events.append({"choice": "More cautious", "at": datetime.now().strftime("%I:%M %p"), "location": result.get("location", "Unknown")})
            st.session_state.feedback_message = "Saved: the next recommendation will lean one step more cautious."
            st.rerun()
        if fb2.button("✓ Keep my style", use_container_width=True):
            st.session_state.feedback_adjustment = 0
            st.session_state.feedback_events.append({"choice": "Keep selected style", "at": datetime.now().strftime("%I:%M %p"), "location": result.get("location", "Unknown")})
            st.session_state.feedback_message = "Saved: future recommendations will use your selected advice style."
            st.rerun()
        if fb3.button("↓ Less cautious", use_container_width=True):
            st.session_state.feedback_adjustment = -1
            st.session_state.feedback_events.append({"choice": "Less cautious", "at": datetime.now().strftime("%I:%M %p"), "location": result.get("location", "Unknown")})
            st.session_state.feedback_message = "Saved: the next recommendation will lean one step more relaxed."
            st.rerun()
        if st.session_state.feedback_message:
            st.success(st.session_state.feedback_message)
        st.markdown(f'<div class="insight"><strong>Current effective style:</strong> {esc(current_preference)}. <strong>Baseline risk:</strong> remains {esc(risk)}.</div>', unsafe_allow_html=True)
        if st.session_state.feedback_events:
            st.markdown("**Recent feedback events**")
            st.dataframe(pd.DataFrame(list(reversed(st.session_state.feedback_events[-8:]))), use_container_width=True, hide_index=True)

    # ========================= Session history =========================
    with history_tab:
        st.markdown('<div class="section-heading">Session history</div><div class="section-subtitle">Compare previous checks kept in this Streamlit session. History is not saved to a database.</div>', unsafe_allow_html=True)
        history = list(reversed(st.session_state.weather_history))
        if not history:
            st.info("Your completed checks will appear here.")
        else:
            hist_df = pd.DataFrame([
                {"Location": x["location"], "Rain probability": f"{x['rain_probability']:.0%}", "Risk": x["risk_level"], "Peak time": x.get("peak_time", "—"), "Checked at": x["checked_at"], "Source": "Sample" if x["demo"] else "Live", "check_id": x.get("check_id", "")}
                for x in history
            ])
            st.dataframe(hist_df.drop(columns=["check_id"]), use_container_width=True, hide_index=True)
            trend_df = pd.DataFrame([{"Check": f"{i+1}. {x['location']}", "Rain probability (%)": x["rain_probability"] * 100} for i, x in enumerate(reversed(history[:10]))])
            if len(trend_df) > 1:
                st.markdown("**Recent check comparison**")
                trend_chart = alt.Chart(trend_df).mark_bar(color="#c62832", cornerRadiusEnd=5).encode(
                    x=alt.X("Check:N", sort=None, title=None, axis=alt.Axis(labelAngle=-28, labelColor="#68748a", domain=False, ticks=False)),
                    y=alt.Y("Rain probability (%):Q", title="Rain probability", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#68748a", gridColor="#edf0f5", domain=False, ticks=False)),
                    tooltip=["Check:N", alt.Tooltip("Rain probability (%):Q", format=".0f")],
                ).properties(height=230, background="#ffffff").configure_view(stroke=None)
                st.altair_chart(trend_chart, use_container_width=True)
            current_id = result.get("_check_id")
            prior = next((item for item in history if item.get("check_id") != current_id and item["location"].strip().casefold() == str(result.get("location", "")).strip().casefold() and item["demo"] == is_demo), None)
            if prior:
                st.markdown("**Previous check for this location and source**")
                c1, c2 = st.columns(2)
                c1.metric("Previous probability", f"{prior['rain_probability']:.0%}", help=prior["checked_at"])
                delta = probability - float(prior["rain_probability"])
                c2.metric("Change since previous check", f"{delta * 100:+.0f} percentage points", delta=f"{delta * 100:+.0f} pp", delta_color="inverse")
            else:
                st.caption("Repeat a check for this location and source to see a side-by-side session comparison.")
            if st.button("Clear session history", type="secondary"):
                st.session_state.weather_history = []
                st.rerun()

else:
    # Friendly empty state for first-time users.
    empty_left, empty_right = st.columns([1.2, 1], gap="large")
    with empty_left:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Your day, planned better</div><h2 style="color:#172033;letter-spacing:-.04em;margin:5px 0 10px">Make a weather-aware decision.</h2><p style="line-height:1.65">Enter a location to analyze tomorrow’s rain probability, identify the peak period, and get a recommendation that you can explain and inspect.</p><div class="insight"><strong>Decision rule:</strong> the peak forecast probability determines the baseline risk band. Personal preferences affect the advice, not the risk classification.</div>', unsafe_allow_html=True)
    with empty_right:
        with st.container(border=True):
            st.markdown('### What the dashboard analyzes')
            st.markdown('<div class="insight"><strong>01 · Peak rain risk</strong><br>Find the time slot with the highest rain probability.</div><div class="insight"><strong>02 · Forecast analytics</strong><br>Review probability trends, temperature variation and risk-band distribution.</div><div class="insight"><strong>03 · Agent reasoning</strong><br>Inspect the specialist role hand-offs and how session feedback personalizes advice.</div>', unsafe_allow_html=True)

with st.expander("About this project"):
    st.markdown(
        """
**Original problem:** Should I carry an umbrella tomorrow in Pune?

- **Unit III:** recent session checks and feedback-aware personalization.
- **Unit IV:** Forecast Analyst → Risk Assessor → Planning Coordinator, with explicit structured outputs.
- **Decision safety:** original deterministic thresholds remain the source of baseline risk; an LLM can explain but cannot override them.
- **Stack:** Streamlit, Python, LangGraph, OpenWeather Forecast API, optional GPT-OSS 20B via Groq.
- **Limitations:** weather forecasts are provided in time slots; feedback and history are session-only; demo values are simulated.
        """
    )
st.markdown('<div class="footer-note">Weather Planning Agent · Streamlit-only UI · Light theme · Offline demo available · Session memory only</div>', unsafe_allow_html=True)
