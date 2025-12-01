@echo off
title Invoice Assistant
echo ========================================
echo Invoice Assistant v1.0.0 (English Interface)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

echo Python detected successfully
echo.

REM Check required files
if not exist "server.py" (
    echo ERROR: server.py not found in current directory
    pause
    exit /b 1
)

if not exist "frontend\dist" (
    echo WARNING: Frontend build directory not found
    echo Please run "npm run build" in the frontend directory first
    pause
    exit /b 1
)

echo Starting Invoice Assistant backend...
echo The server will automatically find an available port
echo.

REM Start the server
python server.py

echo.
echo Invoice Assistant stopped.
pause