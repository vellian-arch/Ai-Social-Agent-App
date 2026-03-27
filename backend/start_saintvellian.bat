@echo off
title Saintvellian AI Multi-Platform Agent

set "PYTHON=%~dp0.venv\Scripts\python.exe"

echo Initializing database...
cd /d %~dp0
"%PYTHON%" database.py

echo Starting FastAPI backend on port 8000...
start cmd /k "title AI Backend && \"%PYTHON%\" -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting ngrok tunnel for port 8000...
start cmd /k "title Ngrok Bridge && ngrok http 8000"

echo Launching Streamlit dashboard...
"%PYTHON%" -m streamlit run dashboard.py

pause
