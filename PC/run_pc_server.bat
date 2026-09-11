@echo off
setlocal enabledelayedexpansion
title WeatherGPT Local Offline Server (PC)
color 0A

echo =======================================================
echo          WeatherGPT Offline AI Engine (PC)
echo =======================================================
echo.

cd /d "%~dp0"

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 goto NO_PYTHON
goto PYTHON_OK

:NO_PYTHON
echo [ERROR] Python is not installed or not added to PATH.
echo Please install Python from python.org and check "Add to PATH".
pause
exit /b 1

:PYTHON_OK
echo [*] Python detected:
python --version

:: 2. Setup Virtual Environment
if exist "venv\Scripts\activate.bat" goto VENV_EXISTS
echo.
echo [*] Creating virtual environment...
python -m venv --system-site-packages venv
if errorlevel 1 (
    echo [WARNING] Could not create venv. Using system Python directly.
    goto SKIP_VENV
)

:VENV_EXISTS
echo [*] Activating virtual environment...
call "venv\Scripts\activate.bat"

:SKIP_VENV

:: 3. Check and Install Dependencies
echo.
echo [*] Checking dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [WARNING] Dependency verification finished with warnings.
)

:: 4. Check for model
if exist "models\*.gguf" goto MODEL_EXISTS

echo.
echo =======================================================
echo   No GGUF model found in models folder!
echo   Launching automated downloader...
echo =======================================================
echo.
python download_model.py

if not exist "models\*.gguf" (
    echo.
    echo [ERROR] Model download was not completed.
    echo Please run python download_model.py to download a model.
    pause
    exit /b 1
)

:MODEL_EXISTS
echo.
echo [OK] GGUF model found in models folder.

:: 5. Display IP Address & ADB instructions for Android connection
echo.
echo =======================================================
echo   CONNECTING YOUR ANDROID PHONE:
echo =======================================================
echo   Option A (USB Cable - Recommended 0-latency):
echo     Run on your PC terminal:
echo       adb reverse tcp:8000 tcp:8000
echo     In WeatherGPT Android Settings, connect to:
echo       http://localhost:8000
echo.
echo   Option B (Same Wi-Fi / Hotspot):
for /f "delims=" %%i in ('python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()" 2^>nul') do (
    echo     Your PC Local IP is: %%i
    echo     In WeatherGPT Android Settings, connect to:
    echo       http://%%i:8000
)
echo =======================================================
echo.
echo [*] Starting WeatherGPT Local Server on port 8000...
echo.

python main.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Server terminated with an error.
    pause
)
