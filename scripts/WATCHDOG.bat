@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — PRODUCTION WATCHDOG
::  Runs main.py directly via venv Python — no EXE, no bundle issues.
::  Keeps the server alive forever. Logs crashes with timestamps.
::  Launched hidden by START_HIDDEN.vbs via Task Scheduler.
::  Use INSTALL_SERVICE.bat to set this up automatically.
:: ═══════════════════════════════════════════════════════════════════
title PizzaClub AI Watchdog
setlocal EnableDelayedExpansion

:: ── Resolve paths ──────────────────────────────────────────────────
set PROJ_DIR=%~dp0
set PYTHON=%PROJ_DIR%venv_311\Scripts\python.exe
set MAIN=%PROJ_DIR%main.py
set LOG_FILE=%PROJ_DIR%watchdog.log
set CFG_FILE=%PROJ_DIR%config.json
set MAX_LOG_KB=512

:: Verify python exists
if not exist "%PYTHON%" (
    echo [ERROR] Python not found at: %PYTHON% >> "%LOG_FILE%"
    echo [ERROR] Python not found. Check venv_311 installation.
    timeout /t 15 /nobreak >nul
    exit /b 1
)

:: Verify main.py exists
if not exist "%MAIN%" (
    echo [ERROR] main.py not found at: %MAIN% >> "%LOG_FILE%"
    echo [ERROR] main.py not found.
    timeout /t 15 /nobreak >nul
    exit /b 1
)

:: ── Read port from config ──────────────────────────────────────────
set APP_PORT=8040
for /f "tokens=2 delims=:," %%a in ('findstr "app_port" "%CFG_FILE%" 2^>nul') do set APP_PORT=%%~a
set APP_PORT=%APP_PORT: =%
if "%APP_PORT%"=="" set APP_PORT=8040

:: ── Rotate log if > 512 KB ────────────────────────────────────────
if exist "%LOG_FILE%" (
    for %%f in ("%LOG_FILE%") do (
        set /a LOG_KB=%%~zf/1024
        if !LOG_KB! GTR %MAX_LOG_KB% (
            copy /y "%LOG_FILE%" "%PROJ_DIR%watchdog.log.bak" >nul 2>&1
            del /f "%LOG_FILE%" >nul 2>&1
        )
    )
)

call :log "========================================"
call :log "PizzaClub Watchdog Started"
call :log "Python : %PYTHON%"
call :log "Script : %MAIN%"
call :log "Port   : %APP_PORT%"
call :log "========================================"

:loop
    call :log "Launching PizzaClub server..."

    :: Kill any lingering Python instance running main.py
    for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr "PID"') do (
        wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
        if !errorlevel!==0 (
            taskkill /f /pid %%p >nul 2>&1
        )
    )
    timeout /t 2 /nobreak >nul

    :: Run main.py — this blocks until the server exits
    "%PYTHON%" "%MAIN%"

    :: If we reach here, the server crashed or was stopped
    call :log "Server exited. Restarting in 10 seconds..."
    timeout /t 10 /nobreak >nul
goto :loop

:log
    for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set D=%%c-%%b-%%a
    for /f "tokens=1-3 delims=:." %%a in ("%time%") do set T=%%a:%%b:%%c
    echo [%D% %T%] %~1 >> "%LOG_FILE%"
    echo [%D% %T%] %~1
    exit /b
