# UniVerse AI — Streamlit Community Cloud Edition
**One Intelligence. Every Discipline. Real-World Impact.**

UniVerse AI is a Streamlit academic workflow platform with account registration/login, database-backed project history, bounded deterministic agent workflows, report downloads, and discipline labs for Computer Science, Engineering (Ohm's law), and fictional Medical Education cases.

## Honest MVP boundaries
- The agent engine is deterministic and does **not** call Gemini or another LLM. Do not describe it as live generative AI.
- The task router is a transparent keyword baseline, not a trained model and has no claimed accuracy score.
- The CS lab creates requirements and test checklists. It never executes arbitrary uploaded code.
- Uploads are validated for this session only and are not persisted.
- Medical cases are fictional and for education only, not diagnosis or treatment.
- Local SQLite is supported. For Streamlit Community Cloud, configure managed PostgreSQL if you need durable project data; the app's local filesystem may reset or be replaced.
- The Streamlit interface accesses SQLAlchemy models directly, so it does not require a separate FastAPI process. The original FastAPI API and React frontend are retained in the repository for development/future use.

## Run locally
Python 3.11+ recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push the **contents** of this project folder to a GitHub repository (not just the ZIP file).
2. Visit https://share.streamlit.io/ and choose **Create app**.
3. Select the repository and branch.
4. Set **Main file path** to `streamlit_app.py` (repository root).
5. Deploy. The app starts with SQLite by default; hosted local SQLite storage is not guaranteed to survive restarts/rebuilds.

### Recommended hosted database
Create a PostgreSQL database with a managed provider, then in Streamlit Cloud open **App → Settings → Secrets** and add TOML values:

```toml
DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
SECRET_KEY = "replace-with-a-long-random-secret"
DEMO_MODE = "true"
```

Use the exact connection URL provided by your database provider. Keep secrets out of GitHub. If the provider supplies `postgres://` or `postgresql://`, convert it to `postgresql+psycopg://` for the installed driver. Use a strong unique secret. The current app creates tables at startup; add migrations before making schema changes in a long-lived production deployment.

## What works
- Registration and login; passwords for Streamlit-created accounts are stored as salted PBKDF2 hashes.
- Per-user project ownership checks on list, read, run, and delete operations.
- Project create, view, search, delete, and persistent workflow history through SQLAlchemy.
- Recorded deterministic workflow steps, status, duration, verification, JSON report download.
- Computer Science requirements/checklist workflow.
- Engineering educational Ohm's law calculator with input validation.
- Fictional medical education case and transparent rubric.
- Transparent keyword task classifier.

## Existing API and React UI
The original FastAPI service remains in `backend/` and React/Vite UI remains in `frontend/`. To run the API locally:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs · Health: http://localhost:8000/health

To run the React frontend in a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

## Tests
```bash
PYTHONPATH=backend pytest backend/tests -q
```

## Safety and production hardening
Before a public production launch, add database migrations, rate limiting, email verification/password reset, monitoring, backups, retention controls, and a dedicated isolated sandbox if code execution is ever required. Never enable arbitrary code execution inside the Streamlit process.
