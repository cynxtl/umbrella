"""Weather API endpoints for Umbrella."""
from __future__ import annotations

import os
from fastapi import APIRouter, Query
from backend.services.weather_service import fetch_weather

router = APIRouter(prefix="/api/weather", tags=["weather"])

@router.get("/forecast")
def get_weather(
    location: str = Query("Pune"),
    demo_mode: bool = Query(True),
    demo_scenario: str = Query("Moderate"),
) -> dict:
    return fetch_weather(
        location=location,
        api_key=os.environ.get("OPENWEATHER_API_KEY"),
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )
