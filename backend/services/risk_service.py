"""Deterministic Risk Engine for Umbrella.

Maintains strict, non-negotiable baseline risk thresholds:
- LOW: pop < 30%
- MODERATE: 30% <= pop < 60%
- HIGH: pop >= 60%
"""
from __future__ import annotations

LOW_THRESHOLD = 0.30
HIGH_THRESHOLD = 0.60
PREFERENCES = ["Conservative", "Balanced", "Relaxed"]

def classify_risk(pop: float) -> tuple[str, str]:
    """Classify baseline rain risk using deterministic thresholds."""
    if pop < LOW_THRESHOLD:
        return "LOW", "No umbrella needed"
    if pop < HIGH_THRESHOLD:
        return "MODERATE", "Carry an umbrella just in case"
    return "HIGH", "Definitely carry an umbrella"

def preference_advice(pop: float, preference: str) -> str:
    """Adjust actionable advice styling based on user preference."""
    pref = preference.lower()
    if pref == "conservative":
        return "Carry an umbrella to be safe" if pop >= 0.20 else "Umbrella optional; rain risk is low"
    if pref == "relaxed":
        return "Carry an umbrella" if pop >= 0.70 else "You can probably leave the umbrella behind"
    return classify_risk(pop)[1]

def effective_preference(base_preference: str, caution_adjustment: int = 0) -> str:
    """Feedback shifts advice style one step without altering baseline risk."""
    try:
        idx = PREFERENCES.index(base_preference.title())
    except ValueError:
        idx = 1
    idx = max(0, min(2, idx - max(-1, min(1, int(caution_adjustment)))))
    return PREFERENCES[idx]
