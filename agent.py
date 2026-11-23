"""Weather Planning Agent: forecast retrieval and role-based recommendation workflow."""
import os, time
from datetime import datetime, timezone, timedelta
from typing import TypedDict, Optional, Literal
import requests
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

GROQ_MODEL = "openai/gpt-oss-20b"
MAX_RETRIES = 3
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"
LOW_THRESHOLD = 0.30
HIGH_THRESHOLD = 0.60
PREFERENCES = ["Conservative", "Balanced", "Relaxed"]

class WeatherState(TypedDict, total=False):
    location: str; attempts: int; max_retries: int
    rain_probability: Optional[float]; temperature: Optional[float]; description: Optional[str]
    peak_rain_time: Optional[str]; peak_time_short: Optional[str]; forecast_date: Optional[str]
    timezone_offset: Optional[int]; forecast_slots: Optional[int]; forecast_timeline: list
    risk_level: Optional[Literal["LOW", "MODERATE", "HIGH"]]; recommendation: Optional[str]
    explanation: Optional[str]; error: Optional[str]; error_kind: Optional[str]; retryable: Optional[bool]
    preference: str; caution_adjustment: int; analyst_output: dict; assessor_output: dict
    coordinator_output: dict; collaboration_trace: list

def classify_risk(pop: float) -> tuple[str, str]:
    """Original baseline thresholds; pop is a fraction from 0 to 1."""
    if pop < LOW_THRESHOLD: return "LOW", "No umbrella needed"
    if pop < HIGH_THRESHOLD: return "MODERATE", "Carry an umbrella just in case"
    return "HIGH", "Definitely carry an umbrella"

def preference_advice(pop: float, preference: str) -> str:
    preference = preference.lower()
    if preference == "conservative": return "Carry an umbrella to be safe" if pop >= .20 else "Umbrella optional; rain risk is low"
    if preference == "relaxed": return "Carry an umbrella" if pop >= .70 else "You can probably leave the umbrella behind"
    return classify_risk(pop)[1]

def effective_preference(base_preference: str, caution_adjustment: int = 0) -> str:
    """Feedback shifts advice style one step, without altering baseline risk."""
    try: idx = PREFERENCES.index(base_preference.title())
    except ValueError: idx = 1
    idx = max(0, min(2, idx - max(-1, min(1, int(caution_adjustment)))))
    return PREFERENCES[idx]

def forecast_analyst(forecast: dict) -> dict:
    """Role 1: extracts forecast facts for the next role."""
    return {"role":"Forecast Analyst", "rain_probability":float(forecast["rain_probability"]),
        "peak_rain_time":str(forecast.get("peak_rain_time", "Not available")),
        "temperature_c":float(forecast.get("temperature", 0)), "conditions":str(forecast.get("description", "Not specified")),
        "forecast_date":str(forecast.get("forecast_date", "Tomorrow")), "slots_reviewed":int(forecast.get("forecast_slots", 0) or 0),
        "status":"Forecast facts prepared"}

def risk_assessor(analyst_output: dict) -> dict:
    """Role 2: applies the original, deterministic risk thresholds."""
    level, recommendation = classify_risk(float(analyst_output["rain_probability"]))
    return {"role":"Risk Assessor", "risk_level":level, "baseline_recommendation":recommendation,
        "thresholds":"LOW <30%; MODERATE 30%–<60%; HIGH ≥60%", "status":"Baseline risk classified"}

def planning_coordinator(analyst_output: dict, assessor_output: dict, preference: str = "Balanced", caution_adjustment: int = 0) -> dict:
    """Role 3: combines risk, human preference and session feedback into a plan."""
    selected = effective_preference(preference, caution_adjustment)
    return {"role":"Planning Coordinator", "selected_preference":selected, "user_selected_preference":preference.title(),
        "feedback_adjustment":max(-1, min(1, int(caution_adjustment))),
        "personalized_recommendation":preference_advice(float(analyst_output["rain_probability"]), selected),
        "baseline_risk_preserved":assessor_output["risk_level"], "status":"Recommendation coordinated"}

def coordinate_recommendation(forecast: dict, preference: str = "Balanced", caution_adjustment: int = 0) -> dict:
    """Run the three specialist roles and expose their structured hand-offs."""
    analyst = forecast_analyst(forecast)
    assessor = risk_assessor(analyst)
    coordinator = planning_coordinator(analyst, assessor, preference, caution_adjustment)
    trace = [{"step":1,"role":analyst["role"],"output":analyst}, {"step":2,"role":assessor["role"],"output":assessor}, {"step":3,"role":coordinator["role"],"output":coordinator}]
    return {"analyst_output":analyst,"assessor_output":assessor,"coordinator_output":coordinator,"collaboration_trace":trace,
        "risk_level":assessor["risk_level"],"recommendation":assessor["baseline_recommendation"],
        "personalized_recommendation":coordinator["personalized_recommendation"],"effective_preference":coordinator["selected_preference"]}

def _entry_local_dt(entry: dict, offset: int) -> datetime:
    return datetime.fromtimestamp(int(entry["dt"]), timezone.utc).replace(tzinfo=None) + timedelta(seconds=offset)

def extract_tomorrow_forecast(data: dict, now_utc: Optional[datetime] = None) -> dict:
    """Filter forecast slots to tomorrow in the city's local timezone."""
    entries = data.get("list") or []
    if not entries: raise ValueError("The weather provider returned no forecast entries.")
    offset = int((data.get("city") or {}).get("timezone", 0))
    now_utc = now_utc or datetime.now(timezone.utc)
    target_date = (now_utc + timedelta(seconds=offset)).date() + timedelta(days=1)
    tomorrow = []
    for entry in entries:
        try:
            local_time = _entry_local_dt(entry, offset)
            if local_time.date() == target_date: tomorrow.append((entry, local_time))
        except (KeyError, TypeError, ValueError, OverflowError): continue
    if not tomorrow: raise ValueError("Tomorrow's forecast is not available in the returned forecast window. Try again later.")
    def pop(entry):
        try: return max(0.0, min(1.0, float(entry.get("pop", 0))))
        except (TypeError, ValueError): return 0.0
    peak_entry, peak_time = max(tomorrow, key=lambda pair: pop(pair[0]))
    try:
        temp = float(peak_entry["main"]["temp"])
        description = str(peak_entry["weather"][0]["description"]).capitalize()
    except (KeyError, IndexError, TypeError, ValueError) as exc: raise ValueError("The forecast data was incomplete. Please try again.") from exc
    timeline = []
    for entry, local_time in tomorrow:
        try: timeline.append({"time":local_time.strftime("%I %p").lstrip("0"),"timestamp":local_time.isoformat(),
            "rain_probability":pop(entry),"temperature":float(entry["main"]["temp"]),"description":str(entry["weather"][0]["description"]).capitalize()})
        except (KeyError, IndexError, TypeError, ValueError): continue
    return {"rain_probability":pop(peak_entry),"temperature":temp,"description":description,
        "peak_rain_time":peak_time.strftime("%A, %I:%M %p"),"peak_time_short":peak_time.strftime("%I:%M %p").lstrip("0"),
        "forecast_date":target_date.isoformat(),"timezone_offset":offset,"forecast_slots":len(tomorrow),"forecast_timeline":timeline}

def fetch_weather(state: WeatherState) -> WeatherState:
    state["attempts"] = state.get("attempts", 0) + 1
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        state.update(error="OpenWeather API key is missing. Add it in the sidebar or .env file.",error_kind="configuration",retryable=False); return state
    try:
        response = requests.get(OPENWEATHER_URL,params={"q":state["location"],"appid":api_key,"units":"metric","cnt":40},timeout=8)
        if response.status_code == 401: state.update(error="OpenWeather rejected the API key. Check that the key is correct and activated.",error_kind="configuration",retryable=False); return state
        if response.status_code == 404: state.update(error=f"Couldn't find '{state['location']}'. Try a city name such as Pune or Pune, IN.",error_kind="location",retryable=False); return state
        if response.status_code == 429: state.update(error="The weather service rate limit was reached. Please wait a little and try again.",error_kind="rate_limit",retryable=True); return state
        response.raise_for_status()
        try: forecast = extract_tomorrow_forecast(response.json())
        except ValueError as exc: state.update(error=str(exc),error_kind="forecast",retryable=False); return state
        state.update(forecast); state["error"] = None; state["retryable"] = False
    except requests.Timeout: state.update(error="The weather service took too long to respond.",error_kind="network",retryable=True)
    except requests.ConnectionError: state.update(error="Couldn't connect to the weather service. Check your internet connection.",error_kind="network",retryable=True)
    except requests.HTTPError: state.update(error="The weather service returned an error. Please try again shortly.",error_kind="service",retryable=True)
    except requests.RequestException: state.update(error="A network error occurred while checking the forecast.",error_kind="network",retryable=True)
    except (ValueError, TypeError): state.update(error="The weather service returned data that couldn't be read.",error_kind="data",retryable=True)
    return state

def should_retry(state: WeatherState) -> str:
    if state.get("error") is None and state.get("rain_probability") is not None: return "decide"
    if state.get("retryable", True) and state.get("attempts", 0) < state.get("max_retries", MAX_RETRIES):
        time.sleep(min(.5 * state.get("attempts", 1), 1.5)); return "retry"
    return "fail"

def decide(state: WeatherState) -> WeatherState:
    state.update(coordinate_recommendation(state,state.get("preference","Balanced"),state.get("caution_adjustment",0)))
    return state

def _fallback_explanation(state: WeatherState) -> str:
    return (f"{state['recommendation']}. Tomorrow's peak forecast rain probability is {state['rain_probability']*100:.0f}% "
        f"({state['risk_level']} risk), around {state.get('peak_rain_time','the forecast period')}. Expected conditions: "
        f"{state.get('description','not specified')}, {state['temperature']:.1f}°C.")

def explain(state: WeatherState) -> WeatherState:
    api_key = os.environ.get("GROQ_API_KEY"); fallback = _fallback_explanation(state)
    if not api_key:
        state["explanation"] = fallback + " (AI explanation unavailable; showing the rule-based summary.)"; state["llm_available"] = False; return state
    try:
        llm = ChatGroq(model=GROQ_MODEL,api_key=api_key,temperature=.2,timeout=12,max_retries=0)
        system = SystemMessage(content="Explain the supplied weather facts in two short sentences. Python already decided the baseline risk and recommendation. Never change them, invent facts, or claim certainty.")
        human = HumanMessage(content=(f"Location: {state['location']}\nForecast date: {state.get('forecast_date')}\nPeak rain time: {state.get('peak_rain_time')}\n"
            f"Rain probability: {state['rain_probability']*100:.0f}%\nRisk: {state['risk_level']}\nRecommendation: {state['recommendation']}\n"
            f"Conditions: {state.get('description')}, {state['temperature']:.1f} C\nExplain this without changing the decision."))
        result = llm.invoke([system,human]); content = result.content
        if isinstance(content,list): content = " ".join(str(p.get("text","")) if isinstance(p,dict) else str(p) for p in content)
        content = str(content).strip(); state["explanation"] = content or fallback; state["llm_available"] = bool(content)
    except Exception:
        state["explanation"] = fallback + " (AI explanation unavailable; showing the rule-based summary.)"; state["llm_available"] = False
    return state

def error_node(state: WeatherState) -> WeatherState:
    state["recommendation"] = "Forecast unavailable"; state["explanation"] = state.get("error") or "Couldn't retrieve tomorrow's forecast. Please try again."; return state

def build_graph():
    graph = StateGraph(WeatherState)
    graph.add_node("fetch_weather",fetch_weather); graph.add_node("decide",decide); graph.add_node("explain",explain); graph.add_node("error",error_node)
    graph.set_entry_point("fetch_weather")
    graph.add_conditional_edges("fetch_weather",should_retry,{"decide":"decide","retry":"fetch_weather","fail":"error"})
    graph.add_edge("decide","explain"); graph.add_edge("explain",END); graph.add_edge("error",END)
    return graph.compile()

def run_agent(location: str, max_retries: int = MAX_RETRIES, preference: str = "Balanced", caution_adjustment: int = 0) -> WeatherState:
    return build_graph().invoke({"location":location.strip(),"attempts":0,"max_retries":max_retries,"preference":preference,"caution_adjustment":caution_adjustment})

def build_demo_result(location: str, scenario: str = "Moderate", preference: str = "Balanced", caution_adjustment: int = 0) -> WeatherState:
    """Offline sample data for a reliable jury demonstration.

    Each scenario's timeline is intentionally consistent with its headline peak
    probability so that the analytics never contradict the recommendation card.
    """
    samples = {
        "Low": (0.15, 23.0, "Cloudy"),
        "Moderate": (0.45, 21.5, "Light rain possible"),
        "High": (0.80, 19.0, "Rain"),
    }
    pop, temp, description = samples[scenario]
    probability_profiles = {
        "Low": [0.05, 0.08, 0.10, 0.12, 0.14, 0.15, 0.11, 0.07],
        "Moderate": [0.10, 0.15, 0.20, 0.35, 0.40, 0.45, 0.30, 0.20],
        "High": [0.25, 0.35, 0.50, 0.65, 0.70, 0.80, 0.65, 0.45],
    }
    times = ["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM"]
    temp_offsets = [-2, -2, -1, 0, 1, 0, -1, -2]
    timeline = [
        {"time": time_label, "rain_probability": slot_probability,
         "temperature": temp + temp_offset, "description": description}
        for time_label, slot_probability, temp_offset in zip(times, probability_profiles[scenario], temp_offsets)
    ]
    forecast = {
        "location": location.strip() or "Demo City",
        "rain_probability": pop,
        "temperature": temp,
        "description": description,
        "peak_rain_time": "Tomorrow, 03:00 PM (sample time)",
        "peak_time_short": "3:00 PM",
        "forecast_date": "Demo forecast",
        "forecast_slots": len(timeline),
        "forecast_timeline": timeline,
        "timezone_offset": 19800,
    }
    forecast.update(coordinate_recommendation(forecast, preference, caution_adjustment))
    forecast["explanation"] = f"Sample scenario: {pop*100:.0f}% rain probability indicates {forecast['risk_level'].lower()} risk. {forecast['recommendation']} Peak probability is around {forecast['peak_time_short']}."
    forecast.update({"attempts":0,"max_retries":MAX_RETRIES,"error":None,"demo_mode":True,"llm_available":False})
    return forecast

if __name__ == "__main__":
    import sys
    result = run_agent(sys.argv[1] if len(sys.argv)>1 else "Pune")
    print(f"\nLocation: {result.get('location')}\nRecommendation: {result.get('recommendation')}\nRisk: {result.get('risk_level')}\nExplanation: {result.get('explanation')}")
