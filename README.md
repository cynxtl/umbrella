# umbrella. — Context-Aware Weather Planning & Adaptive Decision-Making

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%2018%20+%20Vite-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen.svg)](file:///test_agent.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Executive Summary & Product Positioning

**umbrella.** is an intelligent personal weather companion and Agentic AI system engineered for context-aware weather planning, schedule optimization, and adaptive decision-making.

Conventional weather services report raw meteorological numbers, leaving the cognitive burden of decision-making on the user. Generic AI chatbots wrap language models around weather APIs, leading to hallucinated probabilities and uncontrollable advice.

**Umbrella's Core Product Philosophy:**
> *Don't just forecast the weather. Understand the user's goal, evaluate the conditions, compare alternatives, and recommend an actionable plan.*

Umbrella combines a **bounded LangGraph planning orchestrator**, **explicit deterministic tools**, **collaborative specialist roles**, **feedback-aware memory**, and a flagship **Adaptive Plan Comparison** engine wrapped in a **monochromatic dark glassmorphic interface**.

---

## 2. Five Pillars of Agentic AI

Umbrella embodies the five core pillars of an autonomous agent system:

| Pillar | How Umbrella Implements It |
|---|---|
| **1. Goal Understanding** | Multi-turn conversational intent extraction identifies location, activity type (College, Commute, Walking, Outdoor event, Travel), preferred hours, and schedule flexibility. |
| **2. Explicit Tool Usage** | Operates through 4 bounded tools with typed Pydantic contracts: Weather Retrieval, Risk Assessment, Memory Lookup, and Plan Comparison. |
| **3. Adaptive Planning** | Evaluates feasible alternative time windows across the day and recommends lower-risk schedules when rain peaks can be avoided. |
| **4. Adaptive Memory** | Integrates session feedback and local SQLite persistence (`umbrella_memory.db`) to adjust advice style without altering baseline risk thresholds. |
| **5. Explainability** | Exposes a live, auditable chronological execution trace showing exact inputs, outputs, execution durations (ms), and decision evidence. |

---

## 3. System Architecture & Modern Tech Stack

Umbrella 2.0 features a decoupled, production-grade architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT 18 + VITE FRONTEND                 │
│  Monochromatic Glassmorphism (Deep Black #000000)           │
│  Lucide React Icons (No Emojis) · Recharts Probability Curve │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON / HTTP REST
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                       │
│  FastAPI REST API · Pydantic v2 · CORS · Static Dist Serving │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│   LANGGRAPH ORCHESTRATOR     │ │   SQLITE MEMORY PERSISTENCE │
│   7-Node Chronological Graph │ │   User Preferences & SQLite │
│   Specialist Roles Hand-off  │ │   Activity Log (File-Safe)  │
└──────────────┬───────────────┘ └─────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                  BOUNDED DETERMINISTIC TOOLS                 │
│  1. tool_weather_retrieval (OpenWeather API + Offline Demo)  │
│  2. tool_risk_assessment (Deterministic 30% / 60% Rule)      │
│  3. tool_plan_comparison (Adaptive Candidate Sliding Window) │
│  4. tool_memory_lookup (Preference & Feedback Recall)        │
└──────────────────────────────────────────────────────────────┘
```

### Technical Specifications

- **Frontend:** React 18, Vite 5, TypeScript, Tailwind CSS, Lucide React, Recharts.
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, LangGraph, LangChain, ChatGroq.
- **Data & Persistence:** SQLite3 (`umbrella_memory.db`) with parameterized queries and explicit Windows connection lifecycle management.
- **APIs:** OpenWeatherMap 5-day / 3-hour forecast API, Groq LLM API (with deterministic offline fallback).
- **Legacy Fallback:** Original Streamlit application safely preserved in `legacy/app.py`.

---

## 4. Key Capabilities & Technical Features

### 4.1 Flagship Feature: Adaptive Plan Comparison
Users rarely have completely rigid schedules. When planning an activity, Umbrella evaluates candidate time windows shifted across the day:
1. **Preserves Duration:** Keeps activity duration constant.
2. **Respects Constraints:** Restricts candidates to feasible daytime hours (06:00 – 22:00) and allowed user flexibility.
3. **Deterministic Ranking:** Ranks candidates by lower risk category (LOW < MODERATE < HIGH), lower peak rain probability, and minimal schedule shift.
4. **Evidence-Based Rationale:** Highlights exact percentage-point reductions (e.g., *15 pp reduction from 45% to 30%*). If the original window is already best, or if rain risk is uniformly high all day, it clearly informs the user.

### 4.2 Explicit Agent Tools (Typed Contracts)
- **`tool_weather_retrieval`**: Retrieves validated forecast entries from OpenWeather (or scenario-consistent offline demo) with automatic retries and exponential backoff.
- **`tool_risk_assessment`**: Maps user time windows to 3-hour forecast slots, correctly handling timezones and midnight-crossing intervals (e.g., 21:00 to 03:00).
- **`tool_memory_lookup`**: Fetches user preferences and feedback adjustments from SQLite memory.
- **`tool_plan_comparison`**: Generates and ranks alternative candidate schedules based on meteorological facts.

### 4.3 Three Collaborating Specialist Roles
1. **Forecast Analyst**: Prepares meteorological facts (temperature, peak rain timing, conditions, slots reviewed).
2. **Risk Assessor**: Applies deterministic baseline thresholds:
   - **LOW:** $< 30\%$ peak rain probability $\rightarrow$ *No umbrella needed*
   - **MODERATE:** $30\% \le \text{pop} < 60\%$ $\rightarrow$ *Carry an umbrella just in case*
   - **HIGH:** $\ge 60\%$ $\rightarrow$ *Definitely carry an umbrella*
3. **Planning Coordinator**: Harmonizes baseline risk with human advice styles (*Conservative*, *Balanced*, *Relaxed*) and session feedback.

### 4.4 Feedback-Aware Memory & Persistence
- **Dual-Tier Memory**:
  - **Session Memory**: Fast, ephemeral session-state storage for active conversations and feedback events.
  - **SQLite Persistent Memory (`umbrella_memory.db`)**: Local single-user SQLite database with parameterized queries for preferences, feedback history, and activity checks.
- **Controlled Adaptation**: User feedback (`+ More Cautious`, `Standard`, `- Less Cautious`) transparently adjusts the advice style by one step. **Baseline risk thresholds are never modified.**
- **Safe Lifecycle**: Includes a `Reset Session` control that wipes both session and database state.

### 4.5 Security & Safe Credential Handling
- **Zero Global Process Pollution**: User-entered API keys in the UI are injected directly into agent function calls via explicit parameters—never written to shared global `os.environ`.
- **Credential Hygiene**: API keys are excluded from SQLite databases, execution traces, session logs, and `.gitignore` prevents accidental commits of `.env` or `.db` files.

---

## 5. Visual System & Product Identity

The modern frontend follows a restrained, monochromatic, dark glassmorphism design:

- **Product Name:** `umbrella.`
- **Primary Icon:** Lucide React `Umbrella` (zero emojis anywhere in the UI).
- **Background Palette:** Deep black `#000000`, surface card `rgba(255,255,255,0.035)`, border `rgba(255,255,255,0.10)`.
- **Typography:** Primary `#FFFFFF`, secondary `#A3A3A3`, muted `#737373`.
- **Primary Actions:** Solid white buttons with black text.
- **Semantic Risk Accents:** Soft green (`#70C8A0`, Low), warm amber (`#E9BF72`, Moderate), soft red (`#E88C8C`, High).

---

## 6. Installation & Execution

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Node.js 18+ and npm (optional, only required if rebuilding the React frontend)
- Windows PowerShell, macOS Terminal, or Linux Shell

### Quick Start (Production Mode)

The pre-compiled React frontend is already built into `frontend/dist/`. FastAPI serves both the API and the single-page application from a single port.

```powershell
# 1. Clone repository and navigate to directory
git clone https://github.com/cynxtl/umbrella.git
cd umbrella

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Linux/macOS: source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Optional: Configure environment keys
Copy-Item .env.example .env    # On Linux/macOS: cp .env.example .env

# 5. Start the complete application
uvicorn backend.main:app --port 8000
```

Open your browser at **`http://localhost:8000`**.

---

### Development Mode (Hot-Reloading)

If modifying frontend React components or backend endpoints concurrently:

```powershell
# Terminal 1: Backend API
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend Vite Dev Server
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173`** (Vite automatically proxies `/api` requests to port 8000).

---

### Running the Legacy Streamlit App

The original Streamlit application remains fully functional in `legacy/app.py`:

```powershell
streamlit run legacy/app.py
```

---

## 7. Automated Testing & Verification

Run both the modern backend API test suite and the legacy agent verification suite:

```powershell
# 1. Run modern FastAPI & Orchestrator test suite (5 tests)
python -m unittest discover -s backend/tests -v

# 2. Run comprehensive legacy agent & planning test suite (21 tests)
python -m unittest test_agent.py -v
```

**Total automated test coverage:** 26 passing tests covering deterministic boundaries, schedule window math, midnight crossing, plan comparison, memory persistence, offline scenario fidelity, and API error resilience.
