@echo off
TITLE 🌐 Vexel Vision — Remote Access Portal
COLOR 0B

echo.
echo ============================================================
echo   🌐  ENABLING REMOTE KITCHEN ACCESS...
echo ============================================================
echo.

:: 1. Launch the main Pizza Counter in the background
echo [1/2] Starting AI System...
start "" "PizzaVMS.exe"

:: 2. Wait a few seconds for the server to wake up
timeout /t 5 >nul

:: 3. Launch Ngrok Tunnel
echo [2/2] Generating Secure Remote Link...
echo.
echo ------------------------------------------------------------
echo  📱  IMPORTANT: YOUR REMOTE LINK WILL APPEAR BELOW.
echo      LOOK FOR THE LINE STARTING WITH "Forwarding"
echo ------------------------------------------------------------
echo.

set APP_PORT=8040
for /f "tokens=2 delims=:," %%a in ('findstr "app_port" config.json 2^>nul') do set APP_PORT=%%~a
set APP_PORT=%APP_PORT: =%
if "%APP_PORT%"=="" set APP_PORT=8040

:: Use the portable ngrok inside this folder
".\ngrok.exe" http %APP_PORT%

:: If the above fails, try global ngrok
if %ERRORLEVEL% NEQ 0 (
    ngrok http %APP_PORT%
)

pause
