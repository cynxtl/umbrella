# Weather Planning Agent — Jury 2 (Light Dashboard)

A Streamlit-only weather planning dashboard that answers the original question: **Should I carry an umbrella tomorrow in Pune?** It preserves the deterministic baseline thresholds and adds one working concept from Unit III and one from Unit IV.

## What is improved in this version

- **Light visual theme:** white cards, soft grey canvas, restrained red accents and your editable umbrella SVG mark.
- **Forecast analytics:** interactive rain-probability curve with visible 30% and 60% reference thresholds; temperature trend; risk-band distribution; and a slot-by-slot table.
- **Decision insights:** peak risk interpretation, number of slots at moderate/high risk, average slot probability and forecast temperature range.
- **More careful probability interpretation:** the average is labelled as the mean of forecast slots, not a cumulative all-day chance of rain. Probabilities are not added together.
- **Session history analytics:** compare recent checks, chart recent probabilities and compare the same location across checks.
- **Consistent offline demo scenarios:** Low, Moderate and High sample timelines now agree with their headline peak probabilities.

## Unit III — Feedback-aware session memory

- Keeps recent weather checks and feedback in Streamlit session state.
- Lets the user request more cautious advice, keep the selected style, or request less cautious advice.
- Applies transparent, one-step rule-based adjustment to advice style during the current session.
- Baseline risk thresholds are never modified. This is not model training or persistent memory.

## Unit IV — Role-based collaborative workflow

1. **Forecast Analyst** extracts forecast facts and peak timing.
2. **Risk Assessor** applies the original fixed thresholds.
3. **Planning Coordinator** combines risk, user preference and session feedback.

Each role returns structured output that is passed to the next role. The dashboard shows the role hand-offs and an inspectable JSON view for the viva. These are collaborating software roles, not three independent LLMs.

## Setup (Windows PowerShell)

```powershell
cd Weather_Planning_Agent_Jury2_Light_UI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add `OPENWEATHER_API_KEY` to `.env` for live forecasts. `GROQ_API_KEY` is optional. Without a Groq key, the app uses a rule-based explanation. The offline demo needs neither key.

## Run

```powershell
streamlit run app.py
```

Streamlit is configured to launch in light mode through `.streamlit/config.toml`. All interface layout is Streamlit; Altair is used for interactive charts.

## Suggested jury demo

1. Start with **Offline jury demo** enabled and select the Moderate scenario.
2. Show the peak probability card and the rain-probability curve with 30% / 60% threshold lines.
3. Open **Forecast analytics** and explain the risk distribution, temperature trend and slot table.
4. Open **Agent & memory** and show the Forecast Analyst → Risk Assessor → Planning Coordinator hand-offs.
5. Click **More cautious** and show personalized advice changing while baseline risk stays unchanged.
6. Open **Session history** and compare repeated checks; then switch Low / Moderate / High scenarios.
7. If API access is available, turn off offline demo and check a live forecast.

## Tests

```powershell
python -m unittest -v
```

The deterministic unit tests cover threshold boundaries, feedback adjustment, structured role hand-offs, forecast date filtering and scenario-consistent offline timelines.

## Architecture

```text
Streamlit UI
  -> LangGraph forecast retrieval (with transient-error retries)
  -> Forecast Analyst
  -> Risk Assessor (fixed thresholds)
  -> Planning Coordinator (preference + session feedback)
  -> Optional Groq explanation / rule-based fallback
  -> Light Streamlit dashboard + Altair forecast analytics
```

## Limitations

- OpenWeather forecast points are time slots (typically three hours), not minute-by-minute rainfall data.
- Forecast-slot probabilities are not cumulative and must not be added together.
- Feedback and recent checks are session-only; they are not stored in a database.
- Demo values are simulated and labelled as such.
- Baseline risk is deterministic. Personalized advice can differ, but it never overwrites the baseline risk category.
