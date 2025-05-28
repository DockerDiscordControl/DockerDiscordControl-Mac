@echo off
title DDC Heartbeat Monitor
echo.
echo ========================================
echo   DDC Heartbeat Monitor
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if discord.py is installed
python -c "import discord" >nul 2>&1
if errorlevel 1 (
    echo Installing discord.py...
    pip install discord.py
    if errorlevel 1 (
        echo ERROR: Failed to install discord.py
        pause
        exit /b 1
    )
)

REM Check if config.json exists
if not exist "config.json" (
    echo WARNING: config.json not found!
    echo Please copy config.json.example to config.json and edit it.
    pause
    exit /b 1
)

echo Starting DDC Heartbeat Monitor...
echo Press Ctrl+C to stop the monitor
echo.

python ddc_heartbeat_monitor.py

echo.
echo Monitor stopped.
pause 