# Umbrella 2.0 — Context-Aware Weather Planning & Adaptive Decision-Making

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)](file:///test_agent.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Academic Course:** Agentic AI  
> **Final Project Jury:** November 24, 2026  
> **Repository:** [https://github.com/cynxtl/umbrella](https://github.com/cynxtl/umbrella)

---

## 1. Executive Summary & Product Positioning

**Umbrella** is an Agentic AI System designed for context-aware weather planning and adaptive decision-making.

Conventional weather services only report raw meteorological metrics, leaving the cognitive burden of decision-making on the user. Basic AI chatbots wrap language models around weather APIs, leading to unpredictable advice, hallucinated numbers, and uncontrollable overrides.

**Umbrella's Core Product Philosophy:**
> *Don't just forecast the weather. Understand the user's goal, evaluate the conditions, compare alternatives, and recommend an actionable plan.*

Umbrella combines a **bounded LangGraph planning orchestrator**, **explicit deterministic tools**, **collaborative specialist roles**, **feedback-aware memory**, and a flagship **Adaptive Plan Comparison** engine wrapped in a **dark atmospheric glassmorphic interface**.

---

## 2. Five Pillars of Agentic AI

Umbrella embodies the five core characteristics of an autonomous agent:

| Pillar | How Umbrella Implements It |
|---|---|
| **1. Goal Understanding** | Understands destination, activity type (College, Commute, Walking, Outdoor event, Travel), preferred hours, and allowed schedule flexibility. |
| **2. Explicit Tool Usage** | Operates through 4 bounded tools with typed schemas: Weather Retrieval, Risk Assessment, Memory Lookup, and Plan Comparison. |
| **3. Adaptive Planning** | Evaluates feasible alternative time windows and recommends lower-risk schedules when rain peaks can be avoided. |
| **4. Adaptive Memory** | Integrates session feedback and local SQLite persistence (`umbrella_memory.db`) to adjust advice style without altering baseline risk thresholds. |
| **5. Explainability** | Exposes a live, auditable chronological execution trace showing exact inputs, outputs, execution durations, and decision evidence. |

---

## 3. System Architecture & Workflow

```text
User Input: City, Activity, Window (e.g. 3–5 PM), Flexibility (±3h), Preference
                                │
                                ▼
         ┌───────────────────────────────────────────────┐
         │       LangGraph Planning Orchestrator         │
         └──────────────────────┬────────────────────────┘
                                │
      ┌─────────────────────────┼─────────────────────────┐
      ▼                         ▼                         ▼
[Goal Interpreter]      [Memory Lookup Tool]    [Weather Retrieval Tool]
  Identifies goal &       Fetches SQLite &        Queries OpenWeather API
  constraints             session feedback        (or offline jury demo)
                                │                         │
                                └───────────┬─────────────┘
                                            ▼
                                  [Risk Assessment Tool]
                                  Applies deterministic
                                  thresholds to 3h slots
                                            │
               ┌────────────────────────────┴───────────────────────────┐
               ▼                                                        ▼
   [Collaborative Specialist Roles]                          [Plan Comparison Tool]
   • Forecast Analyst (facts)                                Evaluates shifted candidate
   • Risk Assessor (fixed thresholds)                        windows (± hours) to identify
   • Planning Coordinator (personalization)                  lower-risk alternatives
               │                                                        │
               └────────────────────────────┬───────────────────────────┘
                                            ▼
                            [Recommendation Generator]
                            Actionable, context-aware advice
                                            │
                                            ▼
                            [Explainer (ChatGroq / Fallback)]
                            Concise summary of Python's decision
                                            │
                                            ▼
                       [Auditable Execution Trace + UI]
                       Dark Atmospheric Glassmorphism Dashboard
```

---

## 4. Key Capabilities & Technical Features

### 4.1 Flagship Feature: Adaptive Plan Comparison
Users rarely have rigid schedules. When planning an outdoor walk or commute, Umbrella evaluates candidate time windows shifted across the day:
1. **Preserves Duration:** Keeps activity duration constant.
2. **Respects Constraints:** Restricts candidates to feasible daytime hours (06:00 – 22:00) and allowed user flexibility.
3. **Deterministic Ranking:** Ranks candidates by lower risk category (LOW < MODERATE < HIGH), lower peak rain probability, and minimal schedule shift.
4. **Evidence-Based Rationale:** Highlights exact percentage-point reductions (e.g., *15 pp reduction from 45% to 30%*). If the original window is already best, or if rain risk is uniformly high all day, it clearly informs the user.

### 4.2 Explicit Agent Tools (Typed Contracts)
- **`tool_weather_retrieval`**: Retrieves validated forecast entries from OpenWeather (or scenario-consistent offline demo) with automatic retries and exponential backoff.
- **`tool_risk_assessment`**: Maps user time windows to 3-hour forecast slots, correctly handling timezones and midnight-crossing intervals (e.g. 21:00 to 03:00).
- **`tool_memory_lookup`**: Fetches user preferences and feedback adjustments from SQLite memory.
- **`tool_plan_comparison`**: Generates and ranks alternative candidate schedules based on meteorological facts.

### 4.3 Three Collaborating Specialist Roles
Preserved from the Unit IV curriculum, these roles execute with structured handoffs:
1. **Forecast Analyst**: Prepares meteorological facts (temperature, peak rain timing, conditions, slots reviewed).
2. **Risk Assessor**: Applies deterministic baseline thresholds:
   - **LOW:** $< 30\%$ peak rain probability $\rightarrow$ *No umbrella needed*
   - **MODERATE:** $30\% \le \text{pop} < 60\%$ $\rightarrow$ *Carry an umbrella just in case*
   - **HIGH:** $\ge 60\%$ $\rightarrow$ *Definitely carry an umbrella*
3. **Planning Coordinator**: Harmonizes baseline risk with human advice styles (*Conservative*, *Balanced*, *Relaxed*) and session feedback.

### 4.4 Feedback-Aware Memory & Persistence
- **Dual-Tier Memory**:
  - **Session Memory**: Fast, ephemeral session-state storage for active comparisons and feedback events.
  - **SQLite Persistent Memory (`umbrella_memory.db`)**: Local single-user SQLite database with parameterized queries for preferences, feedback history, and activity checks.
- **Controlled Adaptation**: User feedback (`↑ More cautious`, `✓ Keep style`, `↓ Less cautious`) transparently adjusts the advice style by one step. **Baseline risk thresholds are never modified.**
- **Safe Lifecycle**: Includes a `Clear All Memory` control that wipes both session and database state.

### 4.5 Security & Safe Credential Handling
- **Zero Global Process Pollution**: User-entered API keys in the Streamlit UI are injected directly into agent function calls via explicit parameters—never written to shared global `os.environ`.
- **Credential Hygiene**: API keys are excluded from SQLite databases, execution traces, session logs, and `.gitignore` prevents accidental commits of `.env` or `.db` files.

---

## 5. Visual System: Dark Atmospheric Glassmorphism

The dashboard is engineered with a custom dark glassmorphic design system:

| Token Name | Hex Code | Visual Role |
|---|---|---|
| **Midnight** | `#0B1020` | Primary application canvas |
| **Deep Slate** | `#121B2E` | Secondary atmospheric background and sidebar |
| **Atmospheric Blue** | `#182B46` | Subtle radial lighting and glass depth |
| **Ice Blue** | `#82B9EB` | Primary brand accent and interactive highlights |
| **Frost White** | `#E8F3FF` | High-contrast typography and metric values |
| **Muted Blue Grey** | `#9BAEC6` | Secondary labels, descriptions, and axis text |
| **Soft Green** | `#70C8A0` | Low-risk status and live indicators |
| **Soft Amber** | `#E9BF72` | Moderate-risk status and demo badges |
| **Muted Coral** | `#E88C8C` | High-risk warnings and alert thresholds |

### UI Structure (6 Tabs)
1. **Overview**: Daily outlook, actionable recommendation card, at-a-glance rain probability chart, and full-day baseline card.
2. **Activity Planner**: Time-window selector, schedule flexibility setting, and slot overlap statistics.
3. **Compare Plans**: Side-by-side comparison of original vs. recommended alternative schedules with decision evidence.
4. **Forecast Analytics**: Dark Altair probability curves, temperature trends, risk band distribution, and raw slot tables.
5. **Agent Intelligence**: Live 7-step LangGraph execution trace, specialist role cards, and raw JSON export.
6. **Memory & History**: Feedback controls, SQLite persistence inspector, and session history comparisons.

---

## 6. Installation & Execution

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Windows PowerShell, macOS Terminal, or Linux Shell

### Setup

```powershell
# 1. Clone repository and navigate to directory
git clone https://github.com/cynxtl/umbrella.git
cd umbrella

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Linux/macOS: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Optional: Configure local environment keys
Copy-Item .env.example .env    # On Linux/macOS: cp .env.example .env
```

### Launch Application

```powershell
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 7. Automated Testing & Verification

Run the comprehensive offline test suite:

```powershell
python -m unittest -v
```

### Test Suite Coverage (21 Unit & Integration Tests)
- **Baseline Risk Classification (4 tests):** Exact boundary checks (0.299 vs 0.30, 0.599 vs 0.60), risk invariance under preference shifts.
- **Activity Planning (5 tests):** Morning/afternoon window overlap, midnight-crossing time windows, narrow window fallback, activity-specific advice.
- **Adaptive Plan Comparison (3 tests):** Improvement detection, risk reduction percentage point calculation, optimal plan retention, zero flexibility constraint.
- **Agent Orchestrator (5 tests):** 7-step chronological trace validation, deterministic fallback when Groq is absent, mocked HTTP 401/404/429 error handling.
- **Memory Persistence (3 tests):** SQLite preference lifecycle, activity record insertion, table clearing, Windows file-lock safety.
- **Offline Scenarios (1 test):** Verifies that Low, Moderate, and High timelines mathematically agree with headline peaks.

---

## 8. Five-Minute Final Jury Demonstration Script

Follow this script for the academic jury evaluation:

### Minute 1: The Problem & Positioning (Tab 1: Overview)
1. Open the application (starts in **Offline jury demo**, **Moderate** scenario).
2. Point out the dark glassmorphic design and brand emblem.
3. State the core premise: *"Conventional weather apps just dump numbers. Umbrella understands the user's goal, evaluates activity-specific risk, compares alternatives, and delivers an actionable plan."*
4. Show the **Hero Daily Outlook**: Location (Pune), Activity (College 9 AM – 4 PM), Moderate Risk (45%), and Actionable Advice (*"Carry a compact umbrella in your bag"*).
5. Point out the **Baseline Decision Card**: Explain that Python's deterministic thresholds remain the source of truth ($<30\%$ LOW, $30\%-60\%$ MODERATE, $\ge 60\%$ HIGH).

### Minute 2: Flagship Differentiator (Tab 3: Compare Plans)
1. Switch to **Compare Plans** tab.
2. In the Activity Planner form above, enter: Activity: **Walking**, Start: **3:00 PM**, End: **5:00 PM**, Flexibility: **±3 hours flexible**. Click **Plan & Evaluate Weather**.
3. Point out the side-by-side comparison cards:
   - **Original Plan (3:00 PM – 5:00 PM):** 45% peak rain risk (MODERATE).
   - **Recommended Alternative (6:00 PM – 8:00 PM):** 30% peak rain risk (MODERATE).
4. Highlight the **Agent Decision Evidence**: Shows a **15.0 percentage point reduction** in rain risk, steering the user clear of the 3:00 PM rain peak.
5. Note: *"If we give ±7 hours or pick 10 AM, it finds a 20% LOW risk slot. If timing is fixed, it honestly tells the user."*

### Minute 3: Real Agentic Workflow & Trace (Tab 5: Agent Intelligence)
1. Open **Agent Intelligence** tab.
2. Show the **7-Step Chronological Execution Trace**:
   - `Goal interpreted` $\rightarrow$ `Memory looked up` $\rightarrow$ `Weather retrieved` $\rightarrow$ `Risk evaluated` $\rightarrow$ `Alternatives compared` $\rightarrow$ `Recommendation generated` $\rightarrow$ `Explanation delivered`.
3. Expand a step to show the real validated inputs, outputs, status, and duration in milliseconds.
4. Show the **Three Collaborating Specialist Roles**: Forecast Analyst $\rightarrow$ Risk Assessor $\rightarrow$ Planning Coordinator.
5. Explain to the jury: *"This is a genuine LangGraph state graph coordinating explicit tools, not a single monolithic LLM prompt."*

### Minute 4: Adaptation & Memory (Tab 6: Memory & History)
1. Open **Memory & History** tab.
2. Click **↑ More cautious**.
3. Notice the immediate feedback confirmation and the effective advice style shifting to **Conservative**.
4. Return to **Overview**: Show that the personalized recommendation adapted, while the baseline risk level remains **MODERATE** ($45\%$).
5. Scroll down to show the **SQLite Persistent Activity History** table reading from `umbrella_memory.db`.

### Minute 5: Analytical Depth & Live Readiness (Tabs 4 & Sidebar)
1. Open **Forecast Analytics** tab.
2. Show the dark-styled Altair charts: Rain probability curve with 30% and 60% threshold lines, temperature curve, and risk band distribution.
3. Mention the analytical safeguard: *"Forecast-slot probabilities are never added together; the average is labelled as an arithmetic mean of 3-hour blocks."*
4. Toggle **Offline jury demo** off in the sidebar to prove live OpenWeather API capability with credential protection.
5. Conclude: *"Umbrella is reliable, explainable, adaptive, and production-ready."*

---

## 9. Verification Matrix

| Feature | Implemented | Tested | Relevant Files | Remaining Limitations |
|---|:---:|:---:|---|---|
| **Deterministic Risk Engine** | ✅ Yes | ✅ Yes | `agent.py`, `test_agent.py` | Fixed at 30% and 60% thresholds as required by baseline. |
| **Activity-Aware Planning** | ✅ Yes | ✅ Yes | `agent.py`, `app.py`, `test_agent.py` | OpenWeather delivers 3-hour slots; exact minute-by-minute rainfall is not provided by free tier. |
| **Adaptive Plan Comparison** | ✅ Yes | ✅ Yes | `agent.py`, `app.py`, `test_agent.py` | Candidates clamped between 06:00 and 22:00 to avoid recommending overnight slots for general activities. |
| **LangGraph Orchestrator** | ✅ Yes | ✅ Yes | `agent.py`, `test_agent.py` | Bound to 7 explicit deterministic nodes; no unconstrained side effects. |
| **Auditable Execution Trace** | ✅ Yes | ✅ Yes | `agent.py`, `app.py`, `test_agent.py` | Measures execution duration and captures input/output contracts. |
| **Specialist Roles (3 Roles)** | ✅ Yes | ✅ Yes | `agent.py`, `app.py`, `test_agent.py` | Collaborating software components passing structured schemas, not separate paid API calls. |
| **Dark Glassmorphic UI** | ✅ Yes | ✅ Yes | `app.py`, `.streamlit/config.toml` | Built purely on Streamlit without unsupported third-party node packages. |
| **SQLite Persistent Memory** | ✅ Yes | ✅ Yes | `memory.py`, `test_agent.py`, `app.py` | Local single-user SQLite instance; no remote cloud DB required. |
| **Safe Credential Injection** | ✅ Yes | ✅ Yes | `app.py`, `agent.py`, `test_agent.py` | Does not pollute global process environment variables. |
| **Offline Demonstration** | ✅ Yes | ✅ Yes | `agent.py`, `app.py`, `test_agent.py` | Low, Moderate, and High scenarios verified for viva presentations. |

---

## 10. Known Limitations & Future Enhancements

- **Provider Slot Resolution:** OpenWeather Free API provides 5-day forecasts in 3-hour intervals. While Umbrella accurately interpolates and maps user time windows to overlapping slots, it does not invent minute-level precipitation.
- **Calendar & GPS Integration (P2):** Currently, activity timing is entered through the planner form. Future iterations could integrate Google Calendar or Apple Reminders for automated schedule ingestion.
- **Multi-Day Route Planning (P2):** Planning is currently focused on tomorrow's 24-hour cycle. Long-distance transit across multiple geographical waypoints can be added in Umbrella 3.0.

---

## 11. Authors & Acknowledgments

- **Lead Engineer & AI Architect:** Arnav (`arnavkme@gmail.com`)
- **Course:** Agentic AI
- **Frameworks:** Streamlit, LangGraph, Altair, OpenWeather API, Groq LLM
