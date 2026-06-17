@echo off
color 0A
title Pizza & Ice Cream Club VMS — Final Build
echo ============================================================
echo   PIZZA ^& ICE CREAM CLUB — VMS FINAL BUILD
echo   Web-Based Dashboard  ^|  System-Tray Launcher
echo   No Chromium. Browser = user's default browser.
echo ============================================================
echo.

echo [1/5] Stopping any running PizzaVMS instances...
taskkill /f /im PizzaVMS.exe 2>nul
timeout /t 1 /nobreak >nul

echo.
echo [2/5] Cleaning old build artifacts...
rmdir /s /q build_FINAL 2>nul
rmdir /s /q dist_FINAL  2>nul
echo       Done.

echo.
echo [3/5] Activating Python 3.11 environment...
call venv_311\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo   ERROR: Could not activate venv_311. Is it installed?
    pause
    exit /b 1
)

echo.
echo [4/5] Running PyInstaller (this takes a few minutes)...
pyinstaller --clean --distpath dist_FINAL --workpath build_FINAL PizzaVMS_Final.spec

echo.
echo [5/5] Verifying build output...
echo ============================================================
if exist "dist_FINAL\PizzaVMS\PizzaVMS.exe" (
    color 0A
    echo.
    echo   SUCCESS!  Executable compiled.
    echo.
    echo   Location : dist_FINAL\PizzaVMS\PizzaVMS.exe
    echo   Action   : Double-click PizzaVMS.exe to launch the tray app.
    echo              It will start the AI server and open your browser.
    echo.
    echo   TIP: You can create a shortcut to PizzaVMS.exe on the Desktop
    echo        or in the Startup folder for auto-launch on boot.
    echo.
) else (
    color 0C
    echo.
    echo   FAILED.  PizzaVMS.exe was NOT found.
    echo   Please scroll up and check the PyInstaller error output.
    echo.
)
echo ============================================================
pause
