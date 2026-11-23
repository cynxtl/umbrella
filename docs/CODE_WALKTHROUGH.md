# Umbrella Code Walkthrough

This document explains the principal modules, classes, and functions in Umbrella.

---

## 1. Backend Architecture (`backend/`)

### 1.1 `backend/main.py`
- **Purpose**: Application entrypoint for FastAPI. Configures middleware, mounts static files, and routes incoming requests.
- **Key Objects**:
  - `app`: FastAPI instance configured with CORS middleware.
  - `health_check()`: Returns operational status and API configuration state.
  - Static mount: Serves `frontend/dist` when the production build exists.

### 1.2 `backend/api/chat.py`
- **Purpose**: Controller for conversational endpoints.
- **Key Functions**:
  - `handle_chat(request: ChatRequest) -> ChatResponse`:
    - Retrieves or creates the active `session_id`.
    - Merges request overrides into the session context.
    - Appends the user message to session history.
    - Invokes `orchestrate_planning_workflow`.
    - Updates session context and appends the assistant response.
  - `get_history(session_id: str)`: Returns full conversational message history.
  - `reset_history(session_id: str)`: Clears messages and restores default session context.

### 1.3 `backend/services/risk_service.py`
- **Purpose**: Pure deterministic risk classification engine.
- **Key Functions**:
  - `classify_risk(pop: float) -> tuple[str, str]`: Applies fixed thresholds ($<0.30$ LOW, $0.30-0.60$ MODERATE, $\ge 0.60$ HIGH).
  - `preference_advice(pop: float, preference: str) -> str`: Adjusts advice wording based on Conservative, Balanced, or Relaxed style.
  - `effective_preference(base_preference: str, caution_adjustment: int) -> str`: Shuts down silent threshold changes by shifting style index by $\pm 1$ while keeping risk intact.

### 1.4 `backend/services/weather_service.py`
- **Purpose**: Meteorological data acquisition.
- **Key Functions**:
  - `fetch_weather(location, api_key, demo_mode, demo_scenario) -> dict`: Queries OpenWeather forecast endpoint or generates a scenario-consistent offline timeline.
  - `extract_tomorrow_forecast(data: dict, now_utc) -> dict`: Converts UTC forecast slots to the city's local timezone offset, filters to tomorrow, and finds peak probability.
  - `build_demo_forecast(location, scenario) -> dict`: Generates verified 8-slot timelines for Low (15% peak), Moderate (45% peak), and High (80% peak) offline testing.

### 1.5 `backend/services/planning_service.py`
- **Purpose**: Activity window mapping and Adaptive Plan Comparison.
- **Key Functions**:
  - `assess_activity_window(forecast_timeline, window_start, window_end) -> dict`: Maps user start/end times to overlapping 3-hour forecast slots, correctly handling same-day and midnight-crossing intervals.
  - `compare_plans(forecast_timeline, activity_type, start_time, end_time, flexibility_hours, preference, caution_adjustment) -> dict`: Generates candidate schedules shifted by $\pm 1\text{h}$ to $\pm F\text{h}$, ranks candidates by risk band and peak pop, and computes risk reduction in percentage points.
  - `generate_recommendation(activity_type, assessment, preference) -> str`: Contextual advice generator customized for commute, walking, outdoor events, and travel (free of emojis).

### 1.6 `backend/agents/orchestrator.py`
- **Purpose**: Bounded LangGraph planning orchestrator.
- **Key Functions**:
  - `extract_intent_and_plan(query, current_ctx) -> tuple[dict, str]`: Natural language parser extracting activity type, location, time window, and intent.
  - `orchestrate_planning_workflow(...) -> dict`: Executes the 7-step sequence:
    1. Goal interpreted
    2. Memory looked up
    3. Weather retrieved
    4. Risk evaluated (Analyst + Assessor roles)
    5. Alternatives compared (Plan Comparison engine)
    6. Recommendation generated (Coordinator role)
    7. Explanation delivered (ChatGroq LLM or deterministic fallback)
  - Records millisecond execution durations and verified input/output payloads.

---

## 2. Frontend Architecture (`frontend/src/`)

### 2.1 `frontend/src/App.tsx`
- **Purpose**: Root application state manager.
- **State Tracked**:
  - `messages`: Array of conversational messages (user text and assistant payloads).
  - `sessionId`: Persistent browser session identifier stored in `localStorage`.
  - `isLoading`: Loading state for the chat composer.
  - `demoMode` and `demoScenario`: Controls offline simulation vs live weather.
- **Lifecycle**: Manages initial load, session creation, auto-scrolling, and settings synchronization.

### 2.2 `frontend/src/components/WelcomeView.tsx`
- **Purpose**: Landing view displayed before the first conversational turn.
- **Components**:
  - Centered heading: "What are you planning?"
  - Subtitle: "A little foresight for whatever's ahead."
  - 6 interactive prompt cards (e.g. "College schedule", "Evening walk", "Check rain risk").

### 2.3 `frontend/src/components/ChatComposer.tsx`
- **Purpose**: Sticky bottom conversational composer.
- **Features**:
  - Auto-growing multiline textarea.
  - Enter to send, Shift+Enter for newline.
  - High-contrast white circular send button with black arrow icon.
  - Accessibility focus rings and disabled submission states.

### 2.4 `frontend/src/components/ChatMessageItem.tsx`
- **Purpose**: Renders conversation turns and inline contextual widgets.
- **Components**:
  - Conversational assistant text.
  - Inline Weather Card: Actionable recommendation, risk badge, context metadata (location, hours, temperature, conditions).
  - Inline Adaptive Comparison Card: Rendered when alternative schedules are evaluated.
  - Accordion for Forecast Timeline Chart (Recharts).
  - Accordion for Agent Activity Trace (7 steps with ms durations).

### 2.5 `frontend/src/components/ForecastChart.tsx`
- **Purpose**: Interactive Recharts timeline visualization.
- **Features**:
  - 3-hour forecast slots with rain probability curve.
  - Dashed reference lines at 30% (Moderate risk) and 60% (High risk).
  - Monochromatic dark styling with white data points.
  - Custom glassmorphic tooltip showing temperature and weather description.
