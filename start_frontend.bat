@echo off
title React Frontend - Stock Research Analyst
echo ========================================================
echo Starting Vite React Frontend on http://localhost:5173
echo ========================================================
set PATH=C:\Program Files\nodejs;%PATH%
cd /d "%~dp0frontend"
timeout /t 1 /nobreak > nul
start http://localhost:5173
call "C:\Program Files\nodejs\npm.cmd" run dev
pause
