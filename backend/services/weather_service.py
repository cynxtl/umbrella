"""Weather service for Umbrella.

Retrieves validated forecast data from OpenWeather or deterministic offline scenarios.
"""
from __future__ import annotations

import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"

def _entry_local_dt(entry: dict, offset: int) -> datetime:
    return datetime.fromtimestamp(int(entry["dt"]), timezone.utc).replace(tzinfo=None) + timedelta(seconds=offset)

def build_demo_forecast(location: str, scenario: str = "Moderate") -> dict:
    """Offline scenario data with mathematically consistent timelines."""
    samples = {
        "Low": (0.15, 23.0, "Partly cloudy", 3.2, 55),
        "Moderate": (0.45, 21.5, "Light rain possible", 5.0, 72),
        "High": (0.80, 19.0, "Heavy showers", 8.4, 88),
    }
    pop, temp, description, wind, humidity = samples.get(scenario, samples["Moderate"])

    probability_profiles = {
        "Low": [0.05, 0.08, 0.10, 0.12, 0.14, 0.15, 0.11, 0.07],
        "Moderate": [0.10, 0.15, 0.20, 0.35, 0.40, 0.45, 0.30, 0.20],
        "High": [0.25, 0.35, 0.50, 0.65, 0.70, 0.80, 0.65, 0.45],
    }
    times_labels = ["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM"]
    hours_24 = [0, 3, 6, 9, 12, 15, 18, 21]
    temp_offsets = [-2, -2, -1, 0, 1, 0, -1, -2]

    timeline = [
        {
            "time": time_label,
            "hour_24": h24,
            "rain_probability": slot_pop,
            "temperature": temp + toff,
            "description": description if slot_pop >= 0.30 else "Partly cloudy",
            "wind_speed": wind,
            "humidity": humidity,
        }
        for time_label, h24, slot_pop, toff in zip(
            times_labels, hours_24, probability_profiles[scenario], temp_offsets
        )
    ]
    return {
        "location": location.strip() or "Demo City",
        "rain_probability": pop,
        "temperature": temp,
        "description": description,
        "wind_speed": wind,
        "humidity": humidity,
        "peak_rain_time": "Tomorrow, 03:00 PM",
        "peak_time_short": "3:00 PM",
        "forecast_date": "Tomorrow",
        "forecast_slots": len(timeline),
        "forecast_timeline": timeline,
        "timezone_offset": 19800,
        "demo_mode": True,
        "demo_scenario": scenario,
        "error": None,
    }

def extract_tomorrow_forecast(data: dict, now_utc: Optional[datetime] = None) -> dict:
    entries = data.get("list") or []
    if not entries:
        raise ValueError("Weather provider returned no forecast entries.")
    offset = int((data.get("city") or {}).get("timezone", 0))
    now_utc = now_utc or datetime.now(timezone.utc)
    target_date = (now_utc + timedelta(seconds=offset)).date() + timedelta(days=1)
    tomorrow = []
    for entry in entries:
        try:
            local_time = _entry_local_dt(entry, offset)
            if local_time.date() == target_date:
                tomorrow.append((entry, local_time))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    if not tomorrow:
        raise ValueError("Tomorrow's forecast is not available in the returned forecast window.")

    def pop(e):
        try:
            return max(0.0, min(1.0, float(e.get("pop", 0))))
        except (TypeError, ValueError):
            return 0.0

    peak_entry, peak_time = max(tomorrow, key=lambda pair: pop(pair[0]))
    temp = float(peak_entry["main"]["temp"])
    description = str(peak_entry["weather"][0]["description"]).capitalize()
    wind_speed = float(peak_entry.get("wind", {}).get("speed", 0.0))
    humidity = int(peak_entry.get("main", {}).get("humidity", 0))

    timeline = []
    for entry, local_time in tomorrow:
        timeline.append({
            "time": local_time.strftime("%I %p").lstrip("0"),
            "timestamp": local_time.isoformat(),
            "hour_24": local_time.hour,
            "rain_probability": pop(entry),
            "temperature": float(entry["main"]["temp"]),
            "description": str(entry["weather"][0]["description"]).capitalize(),
            "wind_speed": float(entry.get("wind", {}).get("speed", 0.0)),
            "humidity": int(entry.get("main", {}).get("humidity", 0)),
        })

    return {
        "rain_probability": pop(peak_entry),
        "temperature": temp,
        "description": description,
        "wind_speed": wind_speed,
        "humidity": humidity,
        "peak_rain_time": peak_time.strftime("%A, %I:%M %p"),
        "peak_time_short": peak_time.strftime("%I:%M %p").lstrip("0"),
        "forecast_date": target_date.isoformat(),
        "timezone_offset": offset,
        "forecast_slots": len(tomorrow),
        "forecast_timeline": timeline,
        "demo_mode": False,
        "error": None,
    }

def fetch_weather(
    location: str,
    api_key: Optional[str] = None,
    demo_mode: bool = True,
    demo_scenario: str = "Moderate",
) -> dict:
    if demo_mode:
        return build_demo_forecast(location, demo_scenario)

    resolved_key = api_key or os.environ.get("OPENWEATHER_API_KEY")
    if not resolved_key:
        return {
            "error": "OpenWeather API key missing. Configure server keys or enable demo mode.",
            "error_kind": "configuration",
            "retryable": False,
        }

    try:
        response = requests.get(
            OPENWEATHER_URL,
            params={"q": location, "appid": resolved_key, "units": "metric", "cnt": 40},
            timeout=8,
        )
        if response.status_code == 401:
            return {"error": "OpenWeather key rejected.", "error_kind": "configuration", "retryable": False}
        if response.status_code == 404:
            return {"error": f"City '{location}' not found.", "error_kind": "location", "retryable": False}
        if response.status_code == 429:
            return {"error": "OpenWeather rate limit exceeded.", "error_kind": "rate_limit", "retryable": True}
        response.raise_for_status()
        forecast = extract_tomorrow_forecast(response.json())
        forecast["location"] = location.strip()
        return forecast
    except Exception as exc:
        return {"error": str(exc), "error_kind": "network", "retryable": True}
