@echo off
echo Starting Backend and Frontend...

:: Start Backend in a new window
start "Backend Server" cmd /k "start_server.bat"

:: Start Frontend in a new window
start "Frontend Dev Server" cmd /k "cd frontend && npm run dev"

echo.
echo Development environment started!
echo Backend running on http://localhost:8000
echo Frontend will start shortly (usually http://localhost:5173)
echo.
