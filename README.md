# AI Social Agent

AI Social Agent is a Python-based social engagement app with:

- A Streamlit dashboard for operators
- A FastAPI backend for webhook handling and integrations
- Background workers for YouTube, TikTok, notifications, and scheduled tasks

## Project Layout

```text
ai-social-agent/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- integrations/
|   |   |-- legacy/
|   |   |-- services/
|   |   |-- ui/
|   |   `-- workers/
|   |-- scripts/
|   |-- dashboard.py          # compatibility wrapper
|   |-- main.py               # compatibility wrapper
|   |-- database.py           # compatibility wrapper
|   |-- requirements.txt
|   `-- start_saintvellian.bat
|-- uploads/
|-- .env
`-- README.md
```

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

3. Copy the example env file and fill in your real secrets:

```powershell
Copy-Item backend\.env.example backend\.env
```

4. Start the FastAPI backend:

```powershell
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

5. In a second terminal, start the Streamlit dashboard:

```powershell
cd backend
streamlit run dashboard.py
```

## Environment Variables

The app reads its configuration from `.env`. A starter template is available at [backend/.env.example](backend/.env.example).

## Notes

- Real implementation code now lives under `backend/app/`.
- Top-level files in `backend/` are thin compatibility wrappers so existing commands still work.
- `backend/app/api/main.py` is the primary FastAPI app.
- `backend/app/ui/dashboard.py` is the Streamlit UI.
- `backend/app/legacy/webhook_handler.py` is the legacy Flask webhook app.
- SQLite database files and local secrets are intentionally ignored in `.gitignore`.
