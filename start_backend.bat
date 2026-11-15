@echo off
title FastAPI Backend - Stock Research Analyst
echo ========================================================
echo Starting FastAPI Backend on http://127.0.0.1:8000
echo ========================================================
set PYTHONPATH=%~dp0backend
set DISABLE_SQLALCHEMY_CEXT=1
cd /d "%~dp0backend"
call "venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
