@echo off
color 0A
title Pizza Club — Rebuild EXE with Custom Port
echo ============================================================
echo   PIZZA CLUB — REBUILD TO APPLY NEW PORT SETTING
echo   This compiles a NEW PizzaClub.exe that will start the
echo   server on whatever "app_port" you set in config.json.
echo ============================================================
echo.

:: ── 1. Make sure we are in the project root ────────────────────
:: This bat should be run from the project root (next to main.py)
if not exist "main.py" (
    echo ERROR: Run this from the project root folder (where main.py lives).
    pause & exit /b 1
)

echo [1/4] Stopping any running instances...
taskkill /f /im PizzaVMS.exe 2>nul
timeout /t 1 /nobreak >nul

echo.
echo [2/4] Cleaning old build artifacts...
rmdir /s /q build_FINAL 2>nul
rmdir /s /q dist_FINAL  2>nul
echo       Done.

echo.
echo [3/4] Activating Python 3.11 environment...
call venv_311\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo   ERROR: Could not activate venv_311.
    pause & exit /b 1
)

echo.
echo [4/4] Running PyInstaller (takes 3-5 min)...
pyinstaller --clean --distpath dist_FINAL --workpath build_FINAL PizzaVMS_Final.spec

echo.
echo ============================================================
if exist "dist_FINAL\PizzaVMS\PizzaVMS.exe" (
    color 0A
    echo   SUCCESS! New EXE built.
    echo   Location: dist_FINAL\PizzaVMS\PizzaVMS.exe
    echo.
    echo   Copy dist_FINAL\PizzaVMS\ to the machine and
    echo   set "app_port" in config.json to your desired port.
) else (
    color 0C
    echo   FAILED. Check the PyInstaller output above.
)
echo ============================================================
pause
