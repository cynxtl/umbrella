"""
Weather Planning Agent
-----------------------
A small LangGraph agent that decides whether you need an umbrella.

Flow (graph):
    fetch_weather --(success)--> decide --> explain --> END
         |--(fail, retries left)--> fetch_weather   (loop)
         |--(fail, retries exhausted)--> error --> END

State is passed between nodes as a WeatherState TypedDict.
"""

import os
import time
from typing import TypedDict, Optional, Literal

import requests
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GROQ_MODEL = "openai/gpt-oss-20b"
MAX_RETRIES = 3
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Rain-probability thresholds (as fractions, OpenWeather gives 'pop' 0-1)
LOW_THRESHOLD = 0.30      # below this -> LOW
HIGH_THRESHOLD = 0.60     # at/above this -> HIGH; between -> MODERATE


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class WeatherState(TypedDict, total=False):
    location: str
    attempts: int
    max_retries: int

    # populated on success
    rain_probability: Optional[float]   # 0.0 - 1.0
    temperature: Optional[float]        # celsius
    description: Optional[str]          # e.g. "light rain"
    raw_forecast: Optional[dict]

    # decision
    risk_level: Optional[Literal["LOW", "MODERATE", "HIGH"]]
    recommendation: Optional[str]       # "Carry an umbrella" / "No umbrella needed"

    # final output
    explanation: Optional[str]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Node: fetch_weather (with retry counter baked into state)
# ---------------------------------------------------------------------------

def fetch_weather(state: WeatherState) -> WeatherState:
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    attempts = state.get("attempts", 0) + 1
    state["attempts"] = attempts

    if not api_key:
        state["error"] = "Missing OPENWEATHER_API_KEY environment variable."
        return state

    try:
        resp = requests.get(
            OPENWEATHER_URL,
            params={
                "q": state["location"],
                "appid": api_key,
                "units": "metric",
                "cnt": 8,  # next ~24h in 3h steps
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("list"):
            state["error"] = "No forecast data returned for this location."
            return state

        # Use the max rain probability ('pop') over the next 24h window
        # since that's what matters for "should I carry an umbrella".
        entries = data["list"]
        max_pop_entry = max(entries, key=lambda e: e.get("pop", 0))

        state["rain_probability"] = float(max_pop_entry.get("pop", 0.0))
        state["temperature"] = float(entries[0]["main"]["temp"])
        state["description"] = entries[0]["weather"][0]["description"]
        state["raw_forecast"] = data
        state["error"] = None
        return state

    except (requests.RequestException, KeyError, ValueError, IndexError) as e:
        state["error"] = f"Weather API error (attempt {attempts}): {e}"
        return state


def should_retry(state: WeatherState) -> str:
    """Conditional edge after fetch_weather."""
    if state.get("error") is None and state.get("rain_probability") is not None:
        return "decide"
    if state.get("attempts", 0) < state.get("max_retries", MAX_RETRIES):
        time.sleep(1)  # small backoff
        return "retry"
    return "fail"


# ---------------------------------------------------------------------------
# Node: decide (deterministic threshold logic)
# ---------------------------------------------------------------------------

def decide(state: WeatherState) -> WeatherState:
    pop = state["rain_probability"]

    if pop < LOW_THRESHOLD:
        risk = "LOW"
        rec = "No umbrella needed"
    elif pop < HIGH_THRESHOLD:
        risk = "MODERATE"
        rec = "Carry an umbrella just in case"
    else:
        risk = "HIGH"
        rec = "Definitely carry an umbrella"

    state["risk_level"] = risk
    state["recommendation"] = rec
    return state


# ---------------------------------------------------------------------------
# Node: explain (LLM call via Groq — natural language explanation only;
# the decision itself is already made deterministically above)
# ---------------------------------------------------------------------------

def explain(state: WeatherState) -> WeatherState:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        state["explanation"] = (
            f"{state['recommendation']}. Rain probability is "
            f"{state['rain_probability']*100:.0f}% ({state['risk_level']} risk), "
            f"{state['description']}, {state['temperature']:.1f}°C. "
            f"[Set GROQ_API_KEY for a natural-language explanation.]"
        )
        return state

    llm = ChatGroq(model=GROQ_MODEL, api_key=api_key, temperature=0.4)

    system = SystemMessage(content=(
        "You are a concise weather planning assistant. You are given a "
        "pre-computed umbrella recommendation and the raw weather figures "
        "behind it. Do NOT change the recommendation or the risk level — "
        "just explain it naturally in 2-3 short sentences for the user."
    ))
    human = HumanMessage(content=(
        f"Location: {state['location']}\n"
        f"Rain probability: {state['rain_probability']*100:.0f}%\n"
        f"Risk level: {state['risk_level']}\n"
        f"Recommendation: {state['recommendation']}\n"
        f"Conditions: {state['description']}, {state['temperature']:.1f}°C\n\n"
        "Write the explanation."
    ))

    try:
        result = llm.invoke([system, human])
        state["explanation"] = result.content.strip()
    except Exception as e:
        # Graceful fallback if the LLM call itself fails
        state["explanation"] = (
            f"{state['recommendation']}. Rain probability is "
            f"{state['rain_probability']*100:.0f}% ({state['risk_level']} risk), "
            f"{state['description']}, {state['temperature']:.1f}°C. "
            f"[LLM explanation unavailable: {e}]"
        )

    return state


# ---------------------------------------------------------------------------
# Node: error (graceful failure path)
# ---------------------------------------------------------------------------

def error_node(state: WeatherState) -> WeatherState:
    state["recommendation"] = "Unable to determine"
    state["explanation"] = (
        "Sorry — I couldn't fetch the weather forecast after "
        f"{state.get('attempts', 0)} attempt(s). "
        f"Last error: {state.get('error', 'unknown error')}. "
        "Please check the location name and your API keys, then try again."
    )
    return state


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(WeatherState)

    graph.add_node("fetch_weather", fetch_weather)
    graph.add_node("decide", decide)
    graph.add_node("explain", explain)
    graph.add_node("error", error_node)

    graph.set_entry_point("fetch_weather")

    graph.add_conditional_edges(
        "fetch_weather",
        should_retry,
        {
            "decide": "decide",
            "retry": "fetch_weather",
            "fail": "error",
        },
    )

    graph.add_edge("decide", "explain")
    graph.add_edge("explain", END)
    graph.add_edge("error", END)

    return graph.compile()


def run_agent(location: str, max_retries: int = MAX_RETRIES) -> WeatherState:
    """Convenience entry point used by the Streamlit UI."""
    app = build_graph()
    initial_state: WeatherState = {
        "location": location,
        "attempts": 0,
        "max_retries": max_retries,
    }
    final_state = app.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    # Quick CLI smoke test
    import sys
    loc = sys.argv[1] if len(sys.argv) > 1 else "Pune"
    result = run_agent(loc)
    print(f"\nLocation: {loc}")
    print(f"Recommendation: {result.get('recommendation')}")
    print(f"Risk level: {result.get('risk_level')}")
    print(f"Explanation: {result.get('explanation')}")
