@echo off
chcp 65001 >nul
title WeatherGPT Local AI Terminal Chat (PC)
color 0B

cd /d "%~dp0"

echo =======================================================
echo          WeatherGPT Local Terminal Chat
echo =======================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

python chat_cli.py

pause
