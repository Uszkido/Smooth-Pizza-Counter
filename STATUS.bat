@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — STATUS CHECKER
::  Shows live status: running/stopped, port, URLs, uptime
:: ═══════════════════════════════════════════════════════════════════
title PizzaClub — Server Status
COLOR 0B
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo    🍕  PIZZA CLUB AI SERVER — STATUS DASHBOARD
echo    Developed by Vexel Innovations
echo  ============================================================
echo.

:: ── Read port from config ──────────────────────────────────────────
set PROJ_DIR=%~dp0
set APP_PORT=8040
for /f "tokens=2 delims=:," %%a in ('findstr "app_port" "%PROJ_DIR%config.json" 2^>nul') do set APP_PORT=%%~a
set APP_PORT=%APP_PORT: =%
if "%APP_PORT%"=="" set APP_PORT=8040

:: ── Check if Python server process is running ──────────────────────
set RUNNING=0
set SERVER_PID=
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr "PID"') do (
    wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
    if !errorlevel!==0 (
        set RUNNING=1
        set SERVER_PID=%%p
    )
)

if "%RUNNING%"=="1" (
    echo    Process Status : [RUNNING] ✅  (PID: %SERVER_PID%)
) else (
    echo    Process Status : [STOPPED] ❌
)

:: ── Check Task Scheduler registration ─────────────────────────────
schtasks /query /tn "PizzaClub AI Server" >nul 2>&1
if %errorlevel%==0 (
    echo    Autostart      : [REGISTERED] ✅  (starts at boot)
) else (
    echo    Autostart      : [NOT INSTALLED] ⚠️
    echo                     Run INSTALL_SERVICE.bat to enable autostart.
)

:: ── Check firewall rule ───────────────────────────────────────────
netsh advfirewall firewall show rule name="PizzaClub AI Server" >nul 2>&1
if %errorlevel%==0 (
    echo    Firewall       : [OPEN] ✅  (port %APP_PORT% allowed)
) else (
    echo    Firewall       : [BLOCKED] ⚠️  (run INSTALL_SERVICE.bat to fix)
)

:: ── Check if port is actually listening ───────────────────────────
netstat -an 2>nul | find ":%APP_PORT% " | find "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo    Port %APP_PORT%        : [LISTENING] ✅
) else (
    echo    Port %APP_PORT%        : [NOT LISTENING] ❌
)

:: ── Display URLs ──────────────────────────────────────────────────
echo.
echo  -- Access URLs ----------------------------------------------
echo    pizza.lan      : http://pizza.lan:%APP_PORT%
echo    Local          : http://127.0.0.1:%APP_PORT%
echo    Network        : http://%COMPUTERNAME%:%APP_PORT%

:: ── Get local IP ──────────────────────────────────────────────────
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "169.254"') do (
    set IP=%%a
    set IP=!IP: =!
    goto :got_ip
)
:got_ip
if defined IP (
    echo    LAN IP Access   : http://!IP!:%APP_PORT%
)

:: ── Check for ngrok tunnel ────────────────────────────────────────
echo.
echo  ── Remote Access ────────────────────────────────────────────
curl -s http://127.0.0.1:4040/api/tunnels >nul 2>&1
if %errorlevel%==0 (
    echo    Ngrok Tunnel   : [ACTIVE] ✅
    echo    Check http://127.0.0.1:4040 for your public URL
) else (
    echo    Ngrok Tunnel   : [INACTIVE] - run START_REMOTE_ACCESS.bat for remote link
)

:: ── Show config info ──────────────────────────────────────────────
echo.
echo  ── Configuration ────────────────────────────────────────────
set PYTHON=%PROJ_DIR%venv_311\Scripts\python.exe
echo    Python         : %PYTHON%
for /f "tokens=2 delims=:," %%a in ('findstr "branch_name" "%PROJ_DIR%config.json" 2^>nul') do (
    set BRANCH=%%~a
    set BRANCH=!BRANCH: =!
    set BRANCH=!BRANCH:"=!
    goto :got_branch
)
:got_branch
if defined BRANCH echo    Branch Name    : !BRANCH!
echo    Config File    : %PROJ_DIR%config.json
echo    Logs File      : %PROJ_DIR%pizza_logs.json
echo    Watchdog Log   : %PROJ_DIR%watchdog.log

echo.
echo  ── Actions ──────────────────────────────────────────────────
echo    [S] Start server (hidden)   [T] Stop server
echo    [R] Restart server          [B] Open browser
echo    [Q] Quit this checker
echo.
set /p ACTION="  Enter action (or press Enter to exit): "

if /i "%ACTION%"=="S" goto :start_srv
if /i "%ACTION%"=="T" goto :stop_srv
if /i "%ACTION%"=="R" goto :restart_srv
if /i "%ACTION%"=="B" goto :open_browser
goto :done

:start_srv
echo  Starting PizzaClub hidden in background...
wscript.exe "%PROJ_DIR%START_HIDDEN.vbs"
timeout /t 5 /nobreak >nul
start "" "http://pizza.lan:%APP_PORT%"
goto :done

:stop_srv
echo  Stopping PizzaClub...
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr "PID"') do (
    wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
    if !errorlevel!==0 (
        taskkill /f /pid %%p >nul 2>&1
        echo  [OK] Killed PID %%p
    )
)
echo  Done.
goto :done

:restart_srv
echo  Restarting PizzaClub...
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr "PID"') do (
    wmic process %%p get CommandLine 2>nul | findstr /i "main.py" >nul 2>&1
    if !errorlevel!==0 (
        taskkill /f /pid %%p >nul 2>&1
    )
)
timeout /t 2 /nobreak >nul
wscript.exe "%PROJ_DIR%START_HIDDEN.vbs"
timeout /t 5 /nobreak >nul
start "" "http://pizza.lan:%APP_PORT%"
goto :done

:open_browser
start "" "http://pizza.lan:%APP_PORT%"
goto :done

:done
echo.
endlocal
pause
