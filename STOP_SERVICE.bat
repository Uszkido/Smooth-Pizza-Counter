@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — STOP SERVICE
::  Kills the running PizzaClub Python server and watchdog.
::  The autostart task remains registered — restarts on next reboot.
::  To permanently remove autostart, use UNINSTALL_SERVICE.bat.
:: ═══════════════════════════════════════════════════════════════════
title PizzaClub — Stop Server
COLOR 0E
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo    ⏹️  STOPPING PIZZA CLUB AI SERVER
echo  ============================================================
echo.
echo  This will stop the server NOW.
echo  The autostart task is still registered — it will restart on next reboot.
echo  To remove autostart permanently, run UNINSTALL_SERVICE.bat.
echo.

:: Kill any python.exe process running main.py
set KILLED=0
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr "PID"') do (
    wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
    if !errorlevel!==0 (
        taskkill /f /pid %%p >nul 2>&1
        echo  [OK] Killed Python server process (PID %%p)
        set KILLED=1
    )
)

:: Also kill any watchdog cmd running under PizzaClub title
taskkill /f /fi "WINDOWTITLE eq PizzaClub AI Watchdog" >nul 2>&1

if "%KILLED%"=="0" (
    echo  [INFO] No running PizzaClub Python process found.
) else (
    echo  [OK] Server stopped successfully.
)

echo.
echo  Dashboard is no longer accessible.
echo  To restart: double-click START_HIDDEN.vbs
echo  To restart + open browser: run CHANGE_PORT_AND_LAUNCH.bat
echo.
pause
endlocal
