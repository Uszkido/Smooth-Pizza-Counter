@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — FIRST-TIME SETUP
::  Creates venv_311 and installs all required packages.
::  Run this ONCE on a new machine before using any other scripts.
::  Requires Python 3.11 to be installed system-wide.
:: ═══════════════════════════════════════════════════════════════════
title PizzaClub — First Time Setup
COLOR 0B
setlocal

echo.
echo  ============================================================
echo    🍕  PIZZA CLUB AI SERVER — FIRST TIME SETUP
echo    This will create a Python virtual environment and
echo    install all required packages. Takes ~2-5 minutes.
echo  ============================================================
echo.

set PROJ_DIR=%~dp0
set VENV=%PROJ_DIR%venv_311
set REQ=%PROJ_DIR%requirements.txt

:: ── Check Python 3.11 ─────────────────────────────────────────────
py -3.11 --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo  [ERROR] Python 3.11 not found.
    echo.
    echo  Please install Python 3.11 from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause & exit /b 1
)

for /f "tokens=*" %%v in ('py -3.11 --version') do echo  [OK] Found %%v

:: ── Create venv ───────────────────────────────────────────────────
if exist "%VENV%" (
    echo  [INFO] venv_311 already exists — skipping creation.
) else (
    echo.
    echo  [1/3] Creating virtual environment (venv_311)...
    py -3.11 -m venv "%VENV%"
    if %errorlevel% NEQ 0 (
        echo  [ERROR] Failed to create venv.
        pause & exit /b 1
    )
    echo  [OK]   venv_311 created.
)

:: ── Upgrade pip ───────────────────────────────────────────────────
echo.
echo  [2/3] Upgrading pip...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip --quiet
echo  [OK]   pip upgraded.

:: ── Install requirements ──────────────────────────────────────────
echo.
echo  [3/3] Installing packages (this takes a few minutes)...
echo        opencv-python, fastapi, uvicorn, ultralytics, numpy...
echo.
"%VENV%\Scripts\pip.exe" install -r "%REQ%"
if %errorlevel% NEQ 0 (
    echo  [ERROR] Package installation failed.
    echo  Check your internet connection and try again.
    pause & exit /b 1
)

echo.
echo  ============================================================
echo    ✅  SETUP COMPLETE
echo.
echo    Next steps:
echo      1. Edit config.json with your camera IP and branch name
echo      2. Run INSTALL_SERVICE.bat as Administrator
echo         (this registers autostart and launches the server)
echo      3. Or just double-click START_HIDDEN.vbs to run now
echo.
echo    Dashboard will be at: http://127.0.0.1:8040
echo  ============================================================
echo.
pause
endlocal
