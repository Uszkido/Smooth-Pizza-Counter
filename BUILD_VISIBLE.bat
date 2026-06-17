@echo off
color 0A
title Pizza & Ice Cream - Windows Executable Builder
echo ========================================================
echo   FINAL VISIBLE BUILD (Python 3.11)
echo ========================================================
echo.
echo Cleaning up old failed build folders to start fresh...
rmdir /s /q build_PizzaIceCream_FINAL 2>nul
rmdir /s /q dist_PizzaIceCream_FINAL 2>nul

echo.
echo Activating stable Python 3.11 environment...
call venv_311\Scripts\activate.bat

echo.
echo Launching PyInstaller (You will see the process live!)...
pyinstaller --clean --distpath dist_PizzaIceCream_FINAL --workpath build_PizzaIceCream_FINAL PizzaIceCreamApp.spec

echo.
echo ========================================================
if exist "dist_PizzaIceCream_FINAL\PizzaIceCreamApp\PizzaIceCreamApp.exe" (
    color 0A
    echo   SUCCESS! The new executable was created successfully!
    echo   You can find it here:
    echo   --^> dist_PizzaIceCream_FINAL\PizzaIceCreamApp\PizzaIceCreamApp.exe
) else (
    color 0C
    echo   FAILED. Please look at the error messages above.
)
echo ========================================================
pause
