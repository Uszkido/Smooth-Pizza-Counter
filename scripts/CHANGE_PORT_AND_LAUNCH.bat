@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — CHANGE PORT & LAUNCH
::  Reads port from config.json and starts the server hidden.
::  No EXE — runs main.py directly via venv Python.
:: ═══════════════════════════════════════════════════════════════════
TITLE 🍕 PizzaClub — Launch Server
COLOR 0B
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   🍕  PIZZA CLUB — LAUNCH SERVER
echo ============================================================
echo.

set PROJ_DIR=%~dp0
set CFG=%PROJ_DIR%config.json

:: Read port from config.json
set APP_PORT=8040
for /f "tokens=2 delims=:," %%a in ('findstr "app_port" "%CFG%" 2^>nul') do set APP_PORT=%%~a
set APP_PORT=%APP_PORT: =%
if "%APP_PORT%"=="" set APP_PORT=8040

echo   Port from config.json : %APP_PORT%
echo.
echo   To change the port, edit "app_port" in config.json
echo   then restart the server. No rebuild required.
echo.

:: Stop any currently running instance first
echo Stopping any existing instance...
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr "PID"') do (
    wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
    if !errorlevel!==0 (
        taskkill /f /pid %%p >nul 2>&1
        echo Stopped old instance (PID %%p)
    )
)
timeout /t 2 /nobreak >nul

:: Start server hidden via VBS launcher
echo Starting PizzaClub in background (hidden)...
wscript.exe "%PROJ_DIR%START_HIDDEN.vbs"

:: Wait for server to come up
timeout /t 6 /nobreak >nul

:: Open browser
echo Opening dashboard at http://pizza.lan:%APP_PORT%
start "" "http://pizza.lan:%APP_PORT%"

echo.
echo ============================================================
echo   Server is running in the background.
echo   Dashboard : http://pizza.lan:%APP_PORT%
echo   Local     : http://127.0.0.1:%APP_PORT%
echo   Close this window - server will keep running.
echo ============================================================
pause
endlocal
