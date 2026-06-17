@echo off
title Pizza & Ice Cream Club - Starting...
echo ===============================================
echo   Pizza ^& Ice Cream Club - AI Counter
echo ===============================================
echo.
echo  Starting server, please wait...
echo  Once ready, open your browser and go to:
echo.
echo        http://localhost:8000
echo.
echo  Keep this window open while using the app.
echo  Close it to shut down the server.
echo ===============================================
echo.

cd /d "%~dp0"
IF EXIST "venv_311\Scripts\python.exe" (
    venv_311\Scripts\python.exe main.py
) ELSE (
    python main.py
)

echo.
echo Server has stopped.
pause
