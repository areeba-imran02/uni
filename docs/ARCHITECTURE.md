# Architecture and safety notes

- **API:** FastAPI routes with Pydantic input validation. Bearer JWT identifies the account. Every project/run read verifies ownership.
- **Persistence:** SQLAlchemy models for users, projects, workflow runs and agent executions. SQLite is the local default. Tables are created at startup for this MVP.
- **Orchestration:** Bounded synchronous pipeline: Router & Planner → domain specialist tool → independent verification → Final Report Agent. Every recorded step stores its output, status and duration. There is no infinite agent loop.
- **ML:** `classify_task` is a transparent keyword baseline. It does not claim trained-model performance.
- **CS safety:** The server does not execute uploaded code. The CS workflow gives a practical requirements/testing checklist.
- **Engineering:** Simple educational Ohm's law calculations with input checks and stated assumptions; not a certified engineering tool.
- **Medical:** Fictional learning scenario and rubric only; not a clinical decision-support system.
- **Files:** Upload endpoint allowlists extensions and enforces 5 MB, but currently does not persist file content.
- **Provider:** Gemini settings are reserved for a future server-side provider adapter. Deterministic mode is the current execution path.
