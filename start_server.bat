@echo off
echo ==========================================
echo      Klarna Invoice Processor Backend
echo ==========================================
echo.

setlocal enabledelayedexpansion

:: Try to find Python
set "PYTHON="

:: 1. Try 'py' launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
    goto :FOUND
)

:: 2. Try 'python' command (only if it's not the Store stub)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto :FOUND
)

:: 3. Check specific paths
set "POSSIBLE_PATHS="
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;C:\Python312\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;C:\Python311\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;C:\Python310\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;C:\Program Files\Python312\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;C:\Program Files\Python311\python.exe"
set "POSSIBLE_PATHS=!POSSIBLE_PATHS!;C:\Program Files\Python310\python.exe"

for %%p in ("%POSSIBLE_PATHS:;=" "%") do (
    if exist %%p (
        set PYTHON="%%~p"
        goto :FOUND
    )
)

:NOT_FOUND
echo [ERROR] Could not find Python. 
echo Please install Python 3.10+ and add it to your PATH.
echo.
pause
exit /b 1

:FOUND
echo Using Python: %PYTHON%
echo.

echo [INFO] Installing dependencies...
%PYTHON% -m pip install fastapi uvicorn python-multipart pdfplumber pandas openpyxl
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting Server...
echo Server will run at: http://localhost:8000
echo.
echo Keep this window OPEN while using the application.
echo.

%PYTHON% server.py
pause
