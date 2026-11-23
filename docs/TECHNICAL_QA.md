# Umbrella Technical Q&A (Academic & Technical Review)

This document answers anticipated questions during a jury or technical architecture review.

---

### 1. Why use LangGraph instead of a standard linear pipeline?
**Answer:** A linear pipeline cannot cleanly manage state loops, retries with backoff, and multi-turn state transitions without messy conditional code. LangGraph provides a typed StateGraph where each node receives a validated state, updates specific keys, and transitions across conditional edges (e.g. `should_retry` routing transient network errors to retries while routing fatal errors to an error node). This produces a predictable, auditable graph rather than uncontrolled execution.

---

### 2. Why use multiple roles (Forecast Analyst, Risk Assessor, Planning Coordinator)?
**Answer:** In software design, separation of concerns prevents semantic pollution:
- **Forecast Analyst** is strictly an information extractor: it knows nothing about user advice style; its only job is extracting facts from raw API slots.
- **Risk Assessor** is strictly an objective evaluator: it applies mathematical thresholds ($<30\%$, $30-60\%$, $\ge 60\%$) and outputs baseline risk.
- **Planning Coordinator** is a policy harmonizer: it combines the objective risk with the user's advice preference (Conservative, Balanced, Relaxed) and session feedback.
Separating these roles ensures human preferences or LLM prompts cannot silently tamper with underlying risk classifications.

---

### 3. What makes Umbrella an "Agentic AI System"?
**Answer:** Umbrella demonstrates the five fundamental characteristics of an autonomous agent:
1. **Goal Understanding:** Translates conversational user goals into structured temporal constraints.
2. **Explicit Tool Usage:** Calls dedicated tools with typed contracts (Weather Retrieval, Risk Assessment, Plan Comparison, Memory).
3. **Adaptive Planning:** Generates feasible candidate schedules and compares alternatives to avoid rain peaks.
4. **Adaptive Memory:** Adjusts behavior across turns based on user feedback and stored preferences.
5. **Explainability:** Records and displays every executed node, input, output, and duration in an auditable trace.

---

### 4. Where is the Large Language Model (LLM) actually used?
**Answer:** Umbrella intentionally confines the LLM to **communication and explanation**, while keeping **decision-making deterministic**:
- The LLM (OpenAI GPT-OSS 20B via Groq) takes the Python-computed facts (activity, risk level, peak slot, recommended alternative) and writes a concise, natural explanation.
- The LLM **never calculates probabilities, never sets thresholds, and cannot override recommendations**.
- If the Groq API key is absent or unreachable, Umbrella seamlessly falls back to a deterministic rule-based explainer without breaking.

---

### 5. Why are the risk thresholds deterministic?
**Answer:** Meteorological risk has tangible consequences: telling a user not to carry an umbrella when rain probability is 80% because an LLM hallucinated is unacceptable in a production product. Deterministic thresholds ($<30\%$ LOW, $30\%-60\%$ MODERATE, $\ge 60\%$ HIGH) provide a rock-solid, reproducible source of truth that can be verified by automated unit tests.

---

### 6. How does Adaptive Plan Comparison work mathematically?
**Answer:** Given a preferred window $[t_{\text{start}}, t_{\text{end}}]$ with duration $D$:
1. The engine generates candidate windows shifted by $\pm 1\text{h}, \dots, \pm F\text{h}$ within daytime hours ($06:00$ to $22:00$).
2. Overlapping 3-hour forecast slots are identified for each candidate, computing candidate peak rain probability $\text{pop}_i$.
3. Candidates are ranked by:
   $$\text{Rank}(C_i) = (\text{RiskBandRank}(C_i), \text{pop}_i, |\Delta t_i|)$$
4. If the best candidate reduces the risk band (e.g. MODERATE $\rightarrow$ LOW) or reduces peak probability by $\ge 15\text{ percentage points}$, it is recommended. Otherwise, Umbrella confirms the original timing is already optimal.

---

### 7. How is conversation memory maintained across multi-turn follow-ups?
**Answer:** Umbrella uses a dual-tier approach:
- **Session Memory (`backend/services/memory_service.py`)**: An in-memory store tracks active session IDs, preserving the current plan context (`location`, `activity_type`, `start_time`, `end_time`, `flexibility_hours`). When a user asks *"What if I leave at 5?"*, the parser recognizes this as an update to `end_time` while retaining the existing location and activity.
- **SQLite Persistent Memory (`umbrella_memory.db`)**: Saves long-term user preferences (advice style and caution adjustment) and activity records using parameterized SQL queries.

---

### 8. What happens when an external API fails?
**Answer:**
- **OpenWeather Failure:** Handled by `tool_weather_retrieval` with automatic retries for transient HTTP 429/500 errors and timeouts. Fatal errors (401 unauthorized, 404 location not found) route directly to user-friendly error messages without crashing.
- **Groq Failure:** Handled with a try/except block that falls back to the deterministic Python explainer.
- **Offline Mode:** When toggled, the application operates completely offline using mathematical scenario models (Low, Moderate, High), making it 100% resilient for jury presentations.

---

### 9. Why migrate from Streamlit to React + FastAPI?
**Answer:**
- **Performance & State Management:** Streamlit re-executes the entire Python script from top to bottom on every user interaction, causing latency and UI resets. React maintains fine-grained client-side component state, allowing instant typing, smooth animations, and independent accordions.
- **True Conversation-First UX:** React allows natural sticky chat composers, dynamic message bubbling, and nested Recharts visualizations without forced full-page rerenders.
- **Production Decoupling:** Separating the frontend (React/Vite) from the backend (FastAPI/LangGraph) follows real-world SaaS architecture, enabling independent testing, CI/CD, and scalability.
