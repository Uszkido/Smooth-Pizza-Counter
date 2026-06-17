@echo off
:: ═══════════════════════════════════════════════════════════════════
::  PizzaClub AI Server — INSTALL SERVICE
::  Registers PizzaClub as a Windows autostart background service
::  using Task Scheduler. Runs the server HIDDEN on boot — no window.
::  Closing any terminal after this does NOT stop the server.
::  Uses venv Python to run main.py directly — no EXE needed.
:: ═══════════════════════════════════════════════════════════════════
title PizzaClub — Install Autostart Service
COLOR 0B
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo    🍕  PIZZA CLUB AI SERVER — SERVICE INSTALLER
echo    Developed by Vexel Innovations
echo    Closing this window will NOT stop the server.
echo  ============================================================
echo.

:: ── Require Admin ─────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo  [ERROR] This script must be run as Administrator.
    echo.
    echo  Right-click INSTALL_SERVICE.bat and choose
    echo  "Run as administrator", then try again.
    echo.
    pause & exit /b 1
)

:: ── Resolve absolute paths ────────────────────────────────────────
set PROJ_DIR=%~dp0
set PYTHON=%PROJ_DIR%venv_311\Scripts\python.exe
set MAIN=%PROJ_DIR%main.py
set VBS_PATH=%PROJ_DIR%START_HIDDEN.vbs
set WDG_PATH=%PROJ_DIR%WATCHDOG.bat

:: Validate python venv
if not exist "%PYTHON%" (
    echo  [ERROR] venv Python not found at:
    echo  %PYTHON%
    echo  Make sure venv_311 is set up correctly.
    pause & exit /b 1
)

:: Validate main.py
if not exist "%MAIN%" (
    echo  [ERROR] main.py not found at:
    echo  %MAIN%
    pause & exit /b 1
)

:: Validate START_HIDDEN.vbs
if not exist "%VBS_PATH%" (
    echo  [ERROR] START_HIDDEN.vbs not found.
    echo  This file must be in the same folder as the installer.
    pause & exit /b 1
)

:: ── Read port from config ──────────────────────────────────────────
set APP_PORT=8040
for /f "tokens=2 delims=:," %%a in ('findstr "app_port" "%PROJ_DIR%config.json" 2^>nul') do set APP_PORT=%%~a
set APP_PORT=%APP_PORT: =%
if "%APP_PORT%"=="" set APP_PORT=8040

echo  [INFO] Python:    %PYTHON%
echo  [INFO] Script:    %MAIN%
echo  [INFO] App port:  %APP_PORT%
echo  [INFO] Launcher:  %VBS_PATH%
echo.

:: ── Register pizza.lan hostname ────────────────────────────────────
set HOSTS_FILE=C:\Windows\System32\drivers\etc\hosts
set HOSTS_ENTRY=127.0.0.1 pizza.lan
echo  [1/5] Registering pizza.lan hostname...
findstr /i "pizza.lan" "%HOSTS_FILE%" >nul 2>&1
if %errorlevel% NEQ 0 (
    echo %HOSTS_ENTRY% >> "%HOSTS_FILE%"
    echo  [OK]   pizza.lan added to hosts file
) else (
    echo  [OK]   pizza.lan already in hosts file (no change)
)

:: ── Open Windows Firewall ──────────────────────────────────────────
echo  [2/5] Adding Windows Firewall rule for port %APP_PORT%...
netsh advfirewall firewall delete rule name="PizzaClub AI Server" >nul 2>&1
netsh advfirewall firewall add rule ^
    name="PizzaClub AI Server" ^
    dir=in ^
    action=allow ^
    protocol=TCP ^
    localport=%APP_PORT% ^
    description="PizzaClub AI server port - managed by Vexel Innovations" >nul 2>&1
if %errorlevel%==0 (
    echo  [OK]   Firewall rule added for port %APP_PORT%
) else (
    echo  [WARN] Could not add firewall rule
)

:: ── Register Task Scheduler ────────────────────────────────────────
echo.
echo  [3/5] Removing any old scheduled task...
schtasks /delete /tn "PizzaClub AI Server" /f >nul 2>&1

echo  [4/5] Registering autostart task...
::
:: The task runs START_HIDDEN.vbs via wscript.exe
:: This means: no window, runs hidden, detached from any UI
::
schtasks /create ^
    /tn "PizzaClub AI Server" ^
    /tr "wscript.exe \"%VBS_PATH%\"" ^
    /sc ONSTART ^
    /ru "SYSTEM" ^
    /rl HIGHEST ^
    /f ^
    /delay 0000:30 ^
    /description "PizzaClub AI Pizza Counter - hidden background service" >nul 2>&1

if %errorlevel%==0 (
    echo  [OK]   Autostart task registered as SYSTEM (hidden, starts 30s after boot)
) else (
    echo  [WARN] SYSTEM account failed. Trying current user (ONLOGON)...
    schtasks /create ^
        /tn "PizzaClub AI Server" ^
        /tr "wscript.exe \"%VBS_PATH%\"" ^
        /sc ONLOGON ^
        /rl HIGHEST ^
        /f ^
        /delay 0000:30 ^
        /description "PizzaClub AI Pizza Counter" >nul 2>&1
    if !errorlevel!==0 (
        echo  [OK]   Autostart task registered (runs at your login, hidden)
    ) else (
        echo  [ERROR] Task registration failed. Try Task Scheduler manually.
    )
)

:: ── Write SERVER_INFO.txt ──────────────────────────────────────────
echo  [5/5] Writing server configuration summary...
(
    echo PizzaClub AI Server - Service Configuration
    echo =============================================
    echo Installed  : %date% %time%
    echo Python     : %PYTHON%
    echo Script     : %MAIN%
    echo Port       : %APP_PORT%
    echo Dashboard  : http://pizza.lan:%APP_PORT%
    echo LAN URL    : http://pizza.lan:%APP_PORT%
    echo Local URL  : http://127.0.0.1:%APP_PORT%
    echo Task Name  : PizzaClub AI Server
    echo Runs as    : SYSTEM (hidden, no window)
    echo.
    echo IMPORTANT:
    echo   Closing any terminal does NOT stop the server.
    echo   The server runs entirely in the background via Python.
    echo   Access from any LAN device via http://pizza.lan:%APP_PORT%
    echo.
    echo To stop the service : Run STOP_SERVICE.bat (as Admin)
    echo To uninstall        : Run UNINSTALL_SERVICE.bat (as Admin)
    echo To check status     : Run STATUS.bat
) > "%PROJ_DIR%SERVER_INFO.txt"

:: ── Launch hidden immediately ──────────────────────────────────────
echo.
echo  ============================================================
echo    ✅  INSTALLATION COMPLETE
echo  ============================================================
echo.
echo    Dashboard   : http://pizza.lan:%APP_PORT%
echo    Local IP    : http://127.0.0.1:%APP_PORT%
echo    Task Name   : PizzaClub AI Server
echo    Starts      : 30 seconds after Windows boots
echo    Window      : None (completely hidden)
echo    Close this window - the server keeps running.
echo.
echo  Starting the server silently in the background now...
wscript.exe "%VBS_PATH%"
timeout /t 6 /nobreak >nul
echo  Opening browser at http://pizza.lan:%APP_PORT% ...
start "" "http://pizza.lan:%APP_PORT%"

echo.
echo  ============================================================
echo    The server is now running silently in the background.
echo    Close this window any time — it will NOT stop the server.
echo    See SERVER_SETUP_GUIDE.html for full documentation.
echo  ============================================================
echo.
pause
endlocal
