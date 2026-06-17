@echo off
color 0A
title Pizza VMS — Full Production Build
echo ============================================================
echo   PIZZA ^& ICE CREAM CLUB — AI VMS INSTALLER BUILD
echo   Developed by Vexel Innovations
echo ============================================================
echo.

REM ── STEP 1: Kill any running instance ────────────────────────
echo [1/3] Stopping any running instances...
taskkill /f /im PizzaVMS.exe 2>nul
echo Done.

REM ── STEP 2: PyInstaller ───────────────────────────────────────
echo.
echo [2/3] Building native VMS executable with PyInstaller...
echo       (This may take 3-5 minutes — grab a coffee!)
echo.
call venv_311\Scripts\activate.bat

rmdir /s /q build_FINAL 2>nul
rmdir /s /q dist_FINAL  2>nul

pyinstaller --clean --distpath dist_FINAL --workpath build_FINAL PizzaVMS_Final.spec

if not exist "dist_FINAL\PizzaVMS\PizzaVMS.exe" (
    color 0C
    echo.
    echo   !! PYINSTALLER FAILED !! Check errors above.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo   PyInstaller build complete!

REM ── STEP 3: Inno Setup Installer ─────────────────────────────
echo.
echo [3/3] Compiling Inno Setup installer...
echo.

REM Try common Inno Setup 6 install paths
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if %ISCC%=="" (
    color 0E
    echo.
    echo   WARNING: Inno Setup 6 not found.
    echo   Please install it from: https://jrsoftware.org/isdl.php
    echo   Then re-run this script to generate the installer.
    echo.
    echo   Your PizzaVMS folder is ready at:
    echo   dist_FINAL\PizzaVMS\PizzaVMS.exe
    echo ============================================================
    pause
    exit /b 0
)

mkdir dist_Installer 2>nul
%ISCC% PizzaInstaller.iss

echo.
echo ============================================================
if exist "dist_Installer\PizzaVMS_Setup_v3.exe" (
    color 0A
    echo   SUCCESS! Installer created:
    echo   dist_Installer\PizzaVMS_Setup_v3.exe
    echo.
    echo   Install it on any Windows PC to deploy the VMS.
) else (
    color 0C
    echo   INNO SETUP FAILED. PizzaVMS folder is still usable at:
    echo   dist_FINAL\PizzaVMS\PizzaVMS.exe
)
echo ============================================================
pause
