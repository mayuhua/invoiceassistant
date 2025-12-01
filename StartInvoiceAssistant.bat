@echo off
title Invoice Assistant
echo ========================================
echo     Invoice Assistant v1.0 (Final Version)
echo ========================================
echo.

REM Check if the portable directory exists
if not exist "invoice_assistant_portable_1764360404" (
    echo ERROR: Portable version directory not found!
    echo Please ensure invoice_assistant_portable_1764360404 exists.
    pause
    exit /b 1
)

echo Starting Invoice Assistant...
echo.
echo The application will start on port 8080
echo Please wait for the server to initialize...
echo.

REM Change to the portable directory and start the application
cd /d "invoice_assistant_portable_1764360404"
start "Invoice Assistant" cmd /k "start.bat"

echo.
echo ========================================
echo   Application is starting...
echo   Please check the server window for the URL
echo   Usually: http://localhost:8080
echo ========================================
echo.
pause