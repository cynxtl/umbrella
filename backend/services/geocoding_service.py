"""Geocoding service for Umbrella.

Provides canonical geocoding resolution using OpenWeather Geocoding API with a rich,
deterministic canonical database for offline demo scenarios and ambiguous disambiguation.
"""
from __future__ import annotations

import os
import requests
from typing import List, Dict, Any, Optional

OPENWEATHER_GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"

COUNTRY_NAMES = {
    "IN": "India",
    "GB": "United Kingdom",
    "UK": "United Kingdom",
    "US": "United States",
    "CA": "Canada",
    "FR": "France",
    "DE": "Germany",
    "JP": "Japan",
    "AU": "Australia",
    "SG": "Singapore",
    "AE": "United Arab Emirates",
    "NL": "Netherlands",
    "IT": "Italy",
    "ES": "Spain",
    "BR": "Brazil",
    "ZA": "South Africa",
    "NZ": "New Zealand",
    "CH": "Switzerland",
}

# Comprehensive canonical dataset for high-accuracy local matching & offline disambiguation
CANONICAL_LOCATIONS: List[Dict[str, Any]] = [
    # India - Maharashtra & Major Metros
    {"name": "Pune", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 18.5204, "lon": 73.8567, "timezone_offset": 19800},
    {"name": "Mumbai", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 19.0760, "lon": 72.8777, "timezone_offset": 19800},
    {"name": "Nagpur", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 21.1458, "lon": 79.0882, "timezone_offset": 19800},
    {"name": "Nashik", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 19.9975, "lon": 73.7898, "timezone_offset": 19800},
    {"name": "Thane", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 19.2183, "lon": 72.9781, "timezone_offset": 19800},
    {"name": "Navi Mumbai", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 19.0330, "lon": 73.0297, "timezone_offset": 19800},
    {"name": "Kolhapur", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 16.7050, "lon": 74.2433, "timezone_offset": 19800},
    {"name": "Aurangabad", "region": "Maharashtra", "country": "India", "country_code": "IN", "lat": 19.8762, "lon": 75.3433, "timezone_offset": 19800},

    # India - Other Major States
    {"name": "New Delhi", "region": "Delhi", "country": "India", "country_code": "IN", "lat": 28.6139, "lon": 77.2090, "timezone_offset": 19800},
    {"name": "Delhi", "region": "Delhi", "country": "India", "country_code": "IN", "lat": 28.7041, "lon": 77.1025, "timezone_offset": 19800},
    {"name": "Bengaluru", "region": "Karnataka", "country": "India", "country_code": "IN", "lat": 12.9716, "lon": 77.5946, "timezone_offset": 19800},
    {"name": "Hyderabad", "region": "Telangana", "country": "India", "country_code": "IN", "lat": 17.3850, "lon": 78.4867, "timezone_offset": 19800},
    {"name": "Chennai", "region": "Tamil Nadu", "country": "India", "country_code": "IN", "lat": 13.0827, "lon": 80.2707, "timezone_offset": 19800},
    {"name": "Kolkata", "region": "West Bengal", "country": "India", "country_code": "IN", "lat": 22.5726, "lon": 88.3639, "timezone_offset": 19800},
    {"name": "Ahmedabad", "region": "Gujarat", "country": "India", "country_code": "IN", "lat": 23.0225, "lon": 72.5714, "timezone_offset": 19800},
    {"name": "Jaipur", "region": "Rajasthan", "country": "India", "country_code": "IN", "lat": 26.9124, "lon": 75.7873, "timezone_offset": 19800},
    {"name": "Chandigarh", "region": "Punjab", "country": "India", "country_code": "IN", "lat": 30.7333, "lon": 76.7794, "timezone_offset": 19800},
    {"name": "Lucknow", "region": "Uttar Pradesh", "country": "India", "country_code": "IN", "lat": 26.8467, "lon": 80.9462, "timezone_offset": 19800},
    {"name": "Kochi", "region": "Kerala", "country": "India", "country_code": "IN", "lat": 9.9312, "lon": 76.2673, "timezone_offset": 19800},
    {"name": "Goa", "region": "Goa", "country": "India", "country_code": "IN", "lat": 15.2993, "lon": 74.1240, "timezone_offset": 19800},
    {"name": "Indore", "region": "Madhya Pradesh", "country": "India", "country_code": "IN", "lat": 22.7196, "lon": 75.8577, "timezone_offset": 19800},
    {"name": "Bhopal", "region": "Madhya Pradesh", "country": "India", "country_code": "IN", "lat": 23.2599, "lon": 77.4126, "timezone_offset": 19800},
    {"name": "Patna", "region": "Bihar", "country": "India", "country_code": "IN", "lat": 25.5941, "lon": 85.1376, "timezone_offset": 19800},
    {"name": "Surat", "region": "Gujarat", "country": "India", "country_code": "IN", "lat": 21.1702, "lon": 72.8311, "timezone_offset": 19800},
    {"name": "Dehradun", "region": "Uttarakhand", "country": "India", "country_code": "IN", "lat": 30.3165, "lon": 78.0322, "timezone_offset": 19800},

    # Ambiguity Test Cases: London, Paris, Springfield, Aberdeen
    {"name": "London", "region": "England", "country": "United Kingdom", "country_code": "GB", "lat": 51.5074, "lon": -0.1278, "timezone_offset": 0},
    {"name": "London", "region": "Ontario", "country": "Canada", "country_code": "CA", "lat": 42.9849, "lon": -81.2453, "timezone_offset": -18000},

    {"name": "Paris", "region": "Île-de-France", "country": "France", "country_code": "FR", "lat": 48.8566, "lon": 2.3522, "timezone_offset": 3600},
    {"name": "Paris", "region": "Texas", "country": "United States", "country_code": "US", "lat": 33.6609, "lon": -95.5555, "timezone_offset": -21600},

    {"name": "Springfield", "region": "Illinois", "country": "United States", "country_code": "US", "lat": 39.7817, "lon": -89.6501, "timezone_offset": -21600},
    {"name": "Springfield", "region": "Missouri", "country": "United States", "country_code": "US", "lat": 37.2090, "lon": -93.2923, "timezone_offset": -21600},
    {"name": "Springfield", "region": "Massachusetts", "country": "United States", "country_code": "US", "lat": 42.1015, "lon": -72.5898, "timezone_offset": -18000},

    # Global Metros
    {"name": "New York", "region": "New York", "country": "United States", "country_code": "US", "lat": 40.7128, "lon": -74.0060, "timezone_offset": -18000},
    {"name": "San Francisco", "region": "California", "country": "United States", "country_code": "US", "lat": 37.7749, "lon": -122.4194, "timezone_offset": -28800},
    {"name": "Seattle", "region": "Washington", "country": "United States", "country_code": "US", "lat": 47.6062, "lon": -122.3321, "timezone_offset": -28800},
    {"name": "Chicago", "region": "Illinois", "country": "United States", "country_code": "US", "lat": 41.8781, "lon": -87.6298, "timezone_offset": -21600},
    {"name": "Toronto", "region": "Ontario", "country": "Canada", "country_code": "CA", "lat": 43.6532, "lon": -79.3832, "timezone_offset": -18000},
    {"name": "Vancouver", "region": "British Columbia", "country": "Canada", "country_code": "CA", "lat": 49.2827, "lon": -123.1207, "timezone_offset": -28800},
    {"name": "Tokyo", "region": "Tokyo", "country": "Japan", "country_code": "JP", "lat": 35.6762, "lon": 139.6503, "timezone_offset": 32400},
    {"name": "Singapore", "region": "Singapore", "country": "Singapore", "country_code": "SG", "lat": 1.3521, "lon": 103.8198, "timezone_offset": 28800},
    {"name": "Sydney", "region": "New South Wales", "country": "Australia", "country_code": "AU", "lat": -33.8688, "lon": 151.2093, "timezone_offset": 39600},
    {"name": "Melbourne", "region": "Victoria", "country": "Australia", "country_code": "AU", "lat": -37.8136, "lon": 144.9631, "timezone_offset": 39600},
    {"name": "Dubai", "region": "Dubai", "country": "United Arab Emirates", "country_code": "AE", "lat": 25.2048, "lon": 55.2708, "timezone_offset": 14400},
    {"name": "Berlin", "region": "Berlin", "country": "Germany", "country_code": "DE", "lat": 52.5200, "lon": 13.4050, "timezone_offset": 3600},
    {"name": "Amsterdam", "region": "North Holland", "country": "Netherlands", "country_code": "NL", "lat": 52.3676, "lon": 4.9041, "timezone_offset": 3600},
]

def format_display_name(name: str, region: Optional[str], country: str) -> str:
    parts = [name]
    if region and region != name:
        parts.append(region)
    if country:
        parts.append(country)
    return ", ".join(parts)

def search_canonical(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Search the deterministic local canonical dataset."""
    q = query.strip().lower()
    if not q:
        return []

    exact_matches = []
    prefix_matches = []
    substring_matches = []

    for loc in CANONICAL_LOCATIONS:
        name_lower = loc["name"].lower()
        region_lower = (loc.get("region") or "").lower()
        country_lower = loc["country"].lower()
        disp_name = format_display_name(loc["name"], loc.get("region"), loc["country"])

        item = {
            "name": loc["name"],
            "region": loc.get("region"),
            "country": loc["country"],
            "country_code": loc.get("country_code", ""),
            "lat": loc["lat"],
            "lon": loc["lon"],
            "timezone_offset": loc.get("timezone_offset", 0),
            "display_name": disp_name,
        }

        if name_lower == q:
            exact_matches.append(item)
        elif name_lower.startswith(q):
            prefix_matches.append(item)
        elif q in name_lower or q in region_lower or q in country_lower:
            substring_matches.append(item)

    combined = exact_matches + prefix_matches + substring_matches
    # Deduplicate preserving order
    seen = set()
    unique = []
    for c in combined:
        key = (c["name"].lower(), (c["region"] or "").lower(), c["country"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(c)
        if len(unique) >= limit:
            break

    return unique

def search_locations(
    query: str,
    api_key: Optional[str] = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """Geocode city query using OpenWeather API with canonical fallback."""
    q = query.strip()
    if len(q) < 2:
        return []

    resolved_key = api_key or os.environ.get("OPENWEATHER_API_KEY")

    if resolved_key:
        try:
            resp = requests.get(
                OPENWEATHER_GEOCODING_URL,
                params={"q": q, "limit": limit, "appid": resolved_key},
                timeout=5,
            )
            if resp.status_code == 200:
                raw_items = resp.json()
                if isinstance(raw_items, list) and len(raw_items) > 0:
                    results = []
                    seen = set()
                    for item in raw_items:
                        name = item.get("name", q)
                        region = item.get("state")
                        raw_country = item.get("country", "")
                        country = COUNTRY_NAMES.get(raw_country, raw_country)
                        disp_name = format_display_name(name, region, country)
                        key = (name.lower(), (region or "").lower(), country.lower())
                        if key not in seen:
                            seen.add(key)
                            results.append({
                                "name": name,
                                "region": region,
                                "country": country,
                                "country_code": raw_country,
                                "lat": float(item.get("lat", 0.0)),
                                "lon": float(item.get("lon", 0.0)),
                                "timezone_offset": 0,
                                "display_name": disp_name,
                            })
                    if results:
                        return results
        except Exception:
            pass  # Fallback to canonical dataset

    return search_canonical(q, limit=limit)

def get_location_details(location_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve canonical location details for a given city string."""
    matches = search_canonical(location_name, limit=1)
    if matches:
        return matches[0]
    return {
        "name": location_name.title(),
        "region": None,
        "country": "India" if location_name.lower() in ["pune", "mumbai", "delhi"] else "",
        "country_code": "",
        "lat": 0.0,
        "lon": 0.0,
        "timezone_offset": 19800 if location_name.lower() in ["pune", "mumbai", "delhi"] else 0,
        "display_name": location_name.title(),
    }
