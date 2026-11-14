@echo off
title Multi-Agent Stock Research Analyst Launcher
echo ===================================================
echo Starting Multi-Agent Stock Research Analyst...
echo ===================================================

:: Start Backend server in its own persistent window
start "FastAPI Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && .\venv\Scripts\activate && python run.py"

:: Start Frontend server in its own persistent window
start "React Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Waiting for servers to initialize...
ping -n 4 127.0.0.1 >nul

:: Open browser
start http://localhost:5173

echo ===================================================
echo Application started successfully!
echo - Frontend: http://localhost:5173
echo - Backend:  http://localhost:8000/docs
echo ===================================================
ping -n 3 127.0.0.1 >nul
