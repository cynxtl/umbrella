# Weather Planning Agent (Umbrella Advisor)

LangGraph agent that checks the forecast and tells you whether to carry an umbrella.

## Stack
- **LLM**: OpenAI GPT-OSS 20B via **Groq API** (agentic, tool-use capable, 131K context)
- **Weather data**: OpenWeather API (5-day/3-hour forecast endpoint)
- **Orchestration**: LangGraph (stateful graph with retry loop)
- **UI**: Streamlit

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your GROQ_API_KEY and OPENWEATHER_API_KEY
```

Get keys:
- Groq: https://console.groq.com/keys
- OpenWeather: https://openweathermap.org/api (free tier is enough)

## Run

```bash
streamlit run app.py
```

Or test the agent standalone from the CLI:

```bash
python agent.py "Pune"
```

## How it works

```
fetch_weather --(ok)--> decide --> explain --> END
     |--(fail, retries left)--> loop back to fetch_weather
     |--(fail, retries exhausted)--> error --> END
```

- **fetch_weather**: calls OpenWeather, pulls max rain probability (`pop`) over the next ~24h. Retries up to 3 times with a 1s backoff on failure.
- **decide**: pure threshold logic, no LLM involved —
  - `< 30%` → LOW → no umbrella
  - `30–60%` → MODERATE → carry just in case
  - `≥ 60%` → HIGH → definitely carry
- **explain**: Groq LLM writes a short natural-language explanation of the *already-made* decision (doesn't get to override it).
- **error**: if all retries fail, returns a graceful message instead of crashing.

## Notes
- Decision logic is deterministic on purpose — the LLM explains, it doesn't decide. Keeps behavior predictable and easy to grade/demo.
- `WeatherState` (TypedDict in `agent.py`) is the single object passed between all graph nodes.
