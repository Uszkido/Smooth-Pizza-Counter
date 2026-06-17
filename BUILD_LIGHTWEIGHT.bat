@echo off
echo ========================================================
echo   Setting up Lightweight Pizza Counter Build
echo ========================================================
echo.
echo 1. Creating an isolated Python Virtual Environment (venv_light)...
python -m venv venv_light
call venv_light\Scripts\activate.bat

echo.
echo 2. Installing pip updates...
python -m pip install --upgrade pip

echo.
echo 3. Installing CPU-Only PyTorch (Saves 2GB)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo 4. Installing other required libraries (Ultralytics, FastAPI, etc)...
pip install ultralytics fastapi uvicorn requests opencv-python pyinstaller jinja2 python-multipart

echo.
echo 5. Compiling Executable to a safe 'dist_light' directory...
pyinstaller --clean --distpath dist_light --workpath build_light PizzaClub.spec

echo.
echo ========================================================
echo   BUILD COMPLETE!
echo.
echo   Your original build in the "dist" folder was completely ignored.
echo   You can find the new slimmed-down executable inside:
echo   --^> dist_light\PizzaClub
echo ========================================================
