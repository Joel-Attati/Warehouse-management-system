@echo off
title Warehouse Management System Launcher
echo ===================================================
echo   Starting Warehouse Management System (Local Mode)
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "WMS Backend (FastAPI)" cmd /k "set PYTHONPATH=%~dp0backend&& cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Next.js Frontend on http://localhost:3000 ...
start "WMS Frontend (Next.js)" cmd /k "cd frontend && npm.cmd start"

echo.
echo ===================================================
echo   WMS is now launching!
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo   Default Login:
echo     Username: admin
echo     Password: admin123
echo ===================================================
echo.
pause

