"""
Weather Planning Agent — Streamlit UI.

Presentation layer only.  The decision architecture (LangGraph graph, nodes,
thresholds) lives in agent.py and is untouched here.
"""
import os
import streamlit as st
from dotenv import load_dotenv

from agent import run_agent, LOW_THRESHOLD, HIGH_THRESHOLD

load_dotenv()

# Remove the phantom scrollbar that Streamlit shows when the page content is
# shorter than the viewport.  Streamlit's default stMainBlockContainer padding
# (96px top / 160px bottom) is huge and makes even short pages overflow the
# viewport.  Trim it down so the page only scrolls when content truly overflows.
st.markdown(
    """
    <style>
        [data-testid="stMain"] { min-height: auto !important; }
        [data-testid="stMainBlockContainer"] {
            padding-top: 1rem !important;
            padding-bottom: 0 !important;
        }
        html, body { overflow-x: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(page_title="Umbrella Advisor", layout="centered")
st.title("Umbrella Advisor")
st.caption("LangGraph + Groq (GPT-OSS 20B) + OpenWeather")

with st.sidebar:
    st.header("Settings")
    st.caption("API keys loaded from .env — override here for this session.")

    groq_key = st.text_input(
        "GROQ_API_KEY", value=os.environ.get("GROQ_API_KEY", ""), type="password"
    )
    owm_key = st.text_input(
        "OPENWEATHER_API_KEY",
        value=os.environ.get("OPENWEATHER_API_KEY", ""),
        type="password",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    if owm_key:
        os.environ["OPENWEATHER_API_KEY"] = owm_key

    st.divider()
    st.subheader("Decision thresholds")
    st.write(f"LOW:       rain < {LOW_THRESHOLD*100:.0f}%  -> no umbrella")
    st.write(f"MODERATE:  {LOW_THRESHOLD*100:.0f}% - {HIGH_THRESHOLD*100:.0f}%  -> carry just in case")
    st.write(f"HIGH:      rain >= {HIGH_THRESHOLD*100:.0f}%  -> definitely carry")
    st.caption("Logic is deterministic; the LLM only writes the explanation.")

# --- location input ---------------------------------------------------------
location = st.text_input("City / location", placeholder="e.g. Pune, Amsterdam, Tokyo")
go = st.button("Check", type="primary", use_container_width=True)

# --- empty state ------------------------------------------------------------
if not go and not location.strip():
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; padding:2rem; color:#94a3b8;'>"
        "<p>Enter a city above and click Check. "
        "I will look at the 24-hour forecast and tell you whether you need an umbrella.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

# --- main action ------------------------------------------------------------
if go:
    if not location.strip():
        st.warning("Enter a location first.")
    elif not os.environ.get("OPENWEATHER_API_KEY"):
        st.error("Missing OPENWEATHER_API_KEY. Add it in the sidebar or .env file.")
    else:
        with st.spinner("Checking the forecast..."):
            result = run_agent(location.strip())

        if result.get("error") and result.get("rain_probability") is None:
            st.error(result.get("explanation", "Something went wrong."))
        else:
            risk = result.get("risk_level")
            st.subheader(result.get("recommendation", "—"))

            col1, col2, col3 = st.columns(3)
            col1.metric("Rain probability", f"{result['rain_probability']*100:.0f}%")
            col2.metric("Temperature", f"{result['temperature']:.1f}°C")
            col3.metric("Risk level", risk)

            st.write(f"**Conditions:** {result.get('description', '—')}")
            st.info(result.get("explanation", ""))

            with st.expander("Debug: raw state"):
                st.json({k: v for k, v in result.items() if k != "raw_forecast"})

st.divider()
st.caption("Retries up to 3 times on API failure. Decision logic is deterministic; the LLM only writes the explanation.")
