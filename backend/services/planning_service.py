"""Planning service: Activity-aware window assessment and Adaptive Plan Comparison."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.services.risk_service import classify_risk, preference_advice, effective_preference, LOW_THRESHOLD, HIGH_THRESHOLD

def parse_time_str(time_str: str) -> int:
    """Parse time string into minutes from midnight."""
    clean = time_str.strip().upper()
    for fmt in ("%H:%M", "%I:%M %p", "%I %p", "%H"):
        try:
            dt = datetime.strptime(clean, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            pass
    return 9 * 60

def format_minutes_to_time(minutes: int) -> str:
    """Convert minutes from midnight to 12-hour string (e.g. 540 -> '9:00 AM')."""
    minutes = minutes % 1440
    hours = minutes // 60
    mins = minutes % 60
    period = "AM" if hours < 12 else "PM"
    display_hour = hours if 1 <= hours <= 12 else (hours - 12 if hours > 12 else 12)
    return f"{display_hour}:{mins:02d} {period}"

def assess_activity_window(
    forecast_timeline: list[dict],
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
) -> dict:
    """Deterministically map activity window to 3-hour forecast slots."""
    if not forecast_timeline:
        return {
            "peak_pop": 0.0,
            "mean_pop": 0.0,
            "risk_level": "LOW",
            "recommendation": "No umbrella needed",
            "overlapping_slots": [],
            "temp_min": 20.0,
            "temp_max": 20.0,
            "conditions": "Clear",
        }

    if not window_start or not window_end:
        pops = [float(s.get("rain_probability", 0.0)) for s in forecast_timeline]
        peak_pop = max(pops) if pops else 0.0
        mean_pop = sum(pops) / len(pops) if pops else 0.0
        risk_level, rec = classify_risk(peak_pop)
        temps = [float(s.get("temperature", 0.0)) for s in forecast_timeline]
        return {
            "peak_pop": peak_pop,
            "mean_pop": mean_pop,
            "risk_level": risk_level,
            "recommendation": rec,
            "temp_min": min(temps) if temps else 0.0,
            "temp_max": max(temps) if temps else 0.0,
            "conditions": forecast_timeline[0].get("description", "Clear"),
            "overlapping_slots": forecast_timeline,
        }

    start_min = parse_time_str(window_start)
    end_min = parse_time_str(window_end)

    overlapping = []
    for slot in forecast_timeline:
        hour = slot.get("hour_24")
        if hour is None:
            time_label = str(slot.get("time", "12 AM"))
            hour = parse_time_str(time_label) // 60
        slot_start_min = hour * 60
        slot_end_min = slot_start_min + 180

        is_overlapping = False
        if start_min <= end_min:
            if max(slot_start_min, start_min) < min(slot_end_min, end_min):
                is_overlapping = True
        else:
            if max(slot_start_min, start_min) < min(slot_end_min, 1440) or max(slot_start_min, 0) < min(slot_end_min, end_min):
                is_overlapping = True

        if is_overlapping:
            overlapping.append(slot)

    if not overlapping:
        def dist(s):
            h = s.get("hour_24", parse_time_str(str(s.get("time", "12 AM"))) // 60)
            return min(abs(h * 60 - start_min), abs(h * 60 - end_min))
        overlapping = [min(forecast_timeline, key=dist)]

    pops = [float(s.get("rain_probability", 0.0)) for s in overlapping]
    peak_pop = max(pops) if pops else 0.0
    mean_pop = sum(pops) / len(pops) if pops else 0.0
    risk_level, rec = classify_risk(peak_pop)
    temps = [float(s.get("temperature", 0.0)) for s in overlapping]
    peak_slot = max(overlapping, key=lambda s: float(s.get("rain_probability", 0.0)))

    return {
        "window_start": window_start,
        "window_end": window_end,
        "peak_pop": peak_pop,
        "mean_pop": mean_pop,
        "risk_level": risk_level,
        "recommendation": rec,
        "temp_min": min(temps) if temps else 0.0,
        "temp_max": max(temps) if temps else 0.0,
        "conditions": peak_slot.get("description", "Not specified"),
        "peak_slot_time": peak_slot.get("time", ""),
        "overlapping_slots": overlapping,
        "moderate_slots": sum(1 for p in pops if LOW_THRESHOLD <= p < HIGH_THRESHOLD),
        "high_slots": sum(1 for p in pops if p >= HIGH_THRESHOLD),
        "wind_speed_max": max([float(s.get("wind_speed", 0.0)) for s in overlapping]) if overlapping else 0.0,
    }

def compare_plans(
    forecast_timeline: list[dict],
    activity_type: str,
    start_time: str,
    end_time: str,
    flexibility_hours: int = 3,
    preference: str = "Balanced",
    caution_adjustment: int = 0,
) -> dict:
    """Flagship Differentiator: Generates candidate windows and recommends lower-risk alternatives."""
    orig_assessment = assess_activity_window(forecast_timeline, start_time, end_time)
    start_min = parse_time_str(start_time)
    end_min = parse_time_str(end_time)
    duration_min = (end_min - start_min) if end_min >= start_min else (end_min + 1440 - start_min)
    if duration_min <= 0:
        duration_min = 120

    orig_plan = {
        "start_time": format_minutes_to_time(start_min),
        "end_time": format_minutes_to_time(end_min),
        "label": f"{format_minutes_to_time(start_min)} – {format_minutes_to_time(end_min)}",
        "peak_pop": orig_assessment["peak_pop"],
        "rain_probability": orig_assessment["peak_pop"],
        "mean_pop": orig_assessment["mean_pop"],
        "risk_level": orig_assessment["risk_level"],
        "conditions": orig_assessment["conditions"],
        "temp_range": f"{orig_assessment['temp_min']:.1f}–{orig_assessment['temp_max']:.1f}°C",
    }

    if flexibility_hours <= 0:
        return {
            "has_better_alternative": False,
            "original_plan": orig_plan,
            "recommended_plan": orig_plan,
            "risk_reduction_pp": 0.0,
            "why_this_plan": f"Timing is fixed for {activity_type}. No flexibility window was requested.",
            "candidates_evaluated": 1,
            "candidates": [orig_plan],
        }

    candidates = []
    max_shift_min = flexibility_hours * 60
    tested_starts = {start_min}

    for shift in range(-max_shift_min, max_shift_min + 60, 60):
        if shift == 0:
            continue
        c_start = start_min + shift
        if c_start < 6 * 60 or (c_start + duration_min) > 22 * 60:
            continue
        if c_start in tested_starts:
            continue
        tested_starts.add(c_start)

        c_end = c_start + duration_min
        c_assessment = assess_activity_window(
            forecast_timeline,
            format_minutes_to_time(c_start),
            format_minutes_to_time(c_end),
        )
        candidates.append({
            "start_time": format_minutes_to_time(c_start),
            "end_time": format_minutes_to_time(c_end),
            "label": f"{format_minutes_to_time(c_start)} – {format_minutes_to_time(c_end)}",
            "shift_hours": shift / 60,
            "peak_pop": c_assessment["peak_pop"],
            "rain_probability": c_assessment["peak_pop"],
            "mean_pop": c_assessment["mean_pop"],
            "risk_level": c_assessment["risk_level"],
            "conditions": c_assessment["conditions"],
            "temp_range": f"{c_assessment['temp_min']:.1f}–{c_assessment['temp_max']:.1f}°C",
        })

    risk_rank = {"LOW": 1, "MODERATE": 2, "HIGH": 3}
    candidates.sort(key=lambda c: (risk_rank[c["risk_level"]], c["peak_pop"], abs(c["shift_hours"])))

    best_candidate = candidates[0] if candidates else None
    orig_rank = risk_rank[orig_plan["risk_level"]]
    has_better = False
    why = ""

    if best_candidate:
        best_rank = risk_rank[best_candidate["risk_level"]]
        pop_reduction = orig_plan["peak_pop"] - best_candidate["peak_pop"]
        reduction_pp = round(pop_reduction * 100, 1)

        if best_rank < orig_rank or reduction_pp >= 15.0:
            has_better = True
            shift_text = f"{abs(best_candidate['shift_hours']):.0f} hours {'earlier' if best_candidate['shift_hours'] < 0 else 'later'}"
            why = (
                f"Shifting {activity_type.lower()} {shift_text} ({best_candidate['label']}) "
                f"reduces peak rain probability from {orig_plan['peak_pop']:.0%} ({orig_plan['risk_level']} risk) "
                f"to {best_candidate['peak_pop']:.0%} ({best_candidate['risk_level']} risk), avoiding the peak rainfall window."
            )
            recommended_plan = best_candidate
        elif abs(reduction_pp) < 10.0 and orig_plan["risk_level"] == "LOW":
            has_better = False
            why = (
                f"Your selected window ({orig_plan['label']}) already enjoys low rain risk "
                f"({orig_plan['peak_pop']:.0%}). Shifting timing provides minimal additional benefit."
            )
            recommended_plan = orig_plan
        elif orig_plan["risk_level"] == "HIGH" and best_candidate["risk_level"] == "HIGH":
            has_better = False
            why = (
                f"Elevated rain risk (≥60%) persists across all feasible windows within ±{flexibility_hours} hours. "
                f"Shifting provides little relief ({best_candidate['peak_pop']:.0%} vs {orig_plan['peak_pop']:.0%}). "
                f"Consider an indoor venue or carry reliable rain gear."
            )
            recommended_plan = orig_plan
        else:
            has_better = False
            why = (
                f"Your original window ({orig_plan['label']}) is optimal or comparable to alternatives "
                f"within your allowed ±{flexibility_hours} hour flexibility."
            )
            recommended_plan = orig_plan
    else:
        recommended_plan = orig_plan
        reduction_pp = 0.0
        why = "No alternative daytime windows could be generated within constraints."

    return {
        "has_better_alternative": has_better,
        "original_plan": orig_plan,
        "recommended_plan": recommended_plan,
        "risk_reduction_pp": max(0.0, reduction_pp if has_better else 0.0),
        "why_this_plan": why,
        "candidates_evaluated": len(candidates) + 1,
        "candidates": candidates[:4],
    }

def generate_recommendation(
    activity_type: str,
    assessment: dict,
    preference: str,
) -> str:
    """Generate context-aware, actionable advice grounded in the specific activity and rain risk (no emojis)."""
    risk = assessment["risk_level"]
    pop = assessment["peak_pop"]
    act = activity_type.lower()

    if "college" in act or "office" in act or "commute" in act:
        if risk == "HIGH":
            return f"Carry a sturdy umbrella and water-resistant bag. High rain risk ({pop:.0%}) during commute hours."
        if risk == "MODERATE":
            return f"Carry a compact umbrella in your bag. Moderate rain risk ({pop:.0%}) during commute hours."
        return f"Commute looks clear. Rain risk is low ({pop:.0%}); umbrella is optional."

    if "walk" in act or "outdoor" in act or "event" in act:
        if risk == "HIGH":
            return f"High rain risk ({pop:.0%}) during outdoor activity. Strongly recommend rescheduling or seeking shelter."
        if risk == "MODERATE":
            return f"Passing showers possible ({pop:.0%}). Keep a light umbrella handy and monitor sky conditions."
        return f"Great conditions for outdoor plans. Rain risk is minimal ({pop:.0%})."

    if "travel" in act:
        if risk == "HIGH":
            return f"Expect wet travel conditions ({pop:.0%}). Pack full rain gear and allow extra transit time."
        if risk == "MODERATE":
            return f"Keep a travel umbrella accessible. Moderate showers ({pop:.0%}) possible on your route."
        return f"Smooth travel conditions expected. Rain risk is low ({pop:.0%})."

    if risk == "HIGH":
        return f"Definitely carry an umbrella. Peak rain probability reaches {pop:.0%} during your activity."
    if risk == "MODERATE":
        return f"Carry an umbrella just in case. Peak rain probability is {pop:.0%} during your activity."
    return f"No umbrella needed. Peak rain probability is only {pop:.0%} during your activity."
