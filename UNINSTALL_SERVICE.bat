@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — UNINSTALL SERVICE
::  Removes Task Scheduler entry, firewall rule, and stops the process
:: ═══════════════════════════════════════════════════════════════════
title PizzaClub — Uninstall Autostart Service
COLOR 0C
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo    🗑️  PIZZA CLUB AI SERVER — UNINSTALL SERVICE
echo  ============================================================
echo.

:: ── Require Admin ─────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo  [ERROR] This script must be run as Administrator.
    pause & exit /b 1
)

set PROJ_DIR=%~dp0

echo  [1/4] Stopping PizzaClub Python server process...
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr "PID"') do (
    wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
    if !errorlevel!==0 (
        taskkill /f /pid %%p >nul 2>&1
        echo  [OK]   Killed PID %%p
    )
)
echo  [OK]   Process stopped.

echo.
echo  [2/4] Removing pizza.lan from hosts file...
set HOSTS_FILE=C:\Windows\System32\drivers\etc\hosts
set HOSTS_TMP=%TEMP%\hosts_backup.txt
copy /y "%HOSTS_FILE%" "%HOSTS_TMP%" >nul 2>&1
type "%HOSTS_TMP%" | findstr /v /i "pizza.lan" > "%HOSTS_FILE%" 2>nul
echo  [OK]   pizza.lan removed from hosts file.

echo.
echo  [3/4] Removing Task Scheduler entry...
schtasks /delete /tn "PizzaClub AI Server" /f >nul 2>&1
if %errorlevel%==0 (
    echo  [OK]   Scheduled task removed.
) else (
    echo  [INFO] No scheduled task found (already removed).
)

echo.
echo  [4/4] Removing firewall rule...
netsh advfirewall firewall delete rule name="PizzaClub AI Server" >nul 2>&1
echo  [OK]   Firewall rule removed.

if exist "%PROJ_DIR%SERVER_INFO.txt" del /f "%PROJ_DIR%SERVER_INFO.txt" >nul 2>&1

echo.
echo  ============================================================
echo    ✅  SERVICE UNINSTALLED SUCCESSFULLY
echo    PizzaClub will no longer start automatically on boot.
echo    Your data (config.json, pizza_logs.json) is untouched.
echo  ============================================================
echo.
pause
endlocal
