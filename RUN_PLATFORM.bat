@echo off
title Multi-Agent Stock Research Analyst Launcher
echo ======================================================================
echo    STARTING MULTI-AGENT STOCK RESEARCH PLATFORM (MODULE 1)
echo ======================================================================
echo.
echo [1/3] Starting FastAPI Backend Server on http://127.0.0.1:8000...
start "FastAPI Backend (Port 8000)" cmd /k "cd /d %~dp0backend && set PYTHONPATH=%~dp0backend && set DISABLE_SQLALCHEMY_CEXT=1 && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Waiting 2 seconds for backend to initialize database...
timeout /t 2 /nobreak > nul

echo [3/3] Starting React Frontend Server & Opening Browser...
start "React Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && set PATH=C:\Program Files\nodejs;%PATH% && npm run dev"

echo.
echo ======================================================================
echo Platform is launched!
echo - Frontend: http://localhost:5173
echo - Backend API: http://127.0.0.1:8000
echo - Swagger API Docs: http://127.0.0.1:8000/docs
echo ======================================================================
timeout /t 3 /nobreak > nul
start http://localhost:5173
exit

