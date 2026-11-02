@echo off
echo ========================================================
echo Starting Smart Logistics & Route Optimization Platform
echo ========================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "Logistics Backend" cmd /k "set PYTHONPATH=backend&& backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --app-dir backend"

echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
cd frontend
start "Logistics Frontend" cmd /k "node ./node_modules/vite/bin/vite.js"

echo ========================================================
echo App is starting up!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000/docs
echo ========================================================
pause
