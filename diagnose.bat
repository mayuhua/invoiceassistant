@echo off
setlocal enabledelayedexpansion

echo Finding Python...

:: Method 1: Try 'py' launcher (standard on Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found 'py' launcher.
    py diagnose.py
    pause
    exit /b
)

:: Method 2: Try 'python' command
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found 'python' command.
    python diagnose.py
    pause
    exit /b
)

:: Method 3: Check common paths
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
        echo Found Python at: %%p
        %%p diagnose.py
        pause
        exit /b
    )
)

echo.
echo ❌ Could not find Python.
echo Please manually edit this file and set the path to your python.exe
echo.
pause
