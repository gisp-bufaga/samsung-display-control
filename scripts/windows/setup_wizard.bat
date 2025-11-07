@echo off
title Display Control - Setup Wizard
color 0B

echo ======================================
echo   DISPLAY CONTROL SETUP WIZARD
echo ======================================
echo.
echo This wizard will help you configure
echo the Display Control System
echo.
pause
cls

REM Step 1: Python Check
echo ======================================
echo   STEP 1/6: Python Check
echo ======================================
echo.
python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python found:
    python --version
    echo [OK]
) else (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo.
pause

REM Step 2: Tailscale Check
cls
echo ======================================
echo   STEP 2/6: Tailscale Check
echo ======================================
echo.
net start | findstr Tailscale >nul
if %errorlevel%==0 (
    echo Tailscale service: [RUNNING]
    echo.
    echo Your Tailscale IP:
    tailscale ip -4
    echo.
    echo [OK]
) else (
    echo [WARNING] Tailscale not running
    echo Install from: https://tailscale.com/download/windows
    echo.
)
pause

REM Step 3: Directory Setup
cls
echo ======================================
echo   STEP 3/6: Directory Setup
echo ======================================
echo.
echo Creating directories...
if not exist "C:\DisplayControl" mkdir "C:\DisplayControl"
if not exist "C:\DisplayControl\logs" mkdir "C:\DisplayControl\logs"
if not exist "C:\DisplayControl\backups" mkdir "C:\DisplayControl\backups"
echo [OK] Directories created
echo.
pause

REM Step 4: Install Dependencies
cls
echo ======================================
echo   STEP 4/6: Install Dependencies
echo ======================================
echo.
echo Installing Python packages...
echo This may take a few minutes...
echo.
python -m pip install flask flask-socketio samsung-mdc schedule requests python-socketio psutil
echo.
echo [OK] Dependencies installed
echo.
pause

REM Step 5: Display IP Configuration
cls
echo ======================================
echo   STEP 5/6: Display Configuration
echo ======================================
echo.
set /p DISPLAY_IP="Enter display IP address (default: 192.168.1.100): "
if "%DISPLAY_IP%"=="" set DISPLAY_IP=192.168.1.100

echo.
echo Testing connection to %DISPLAY_IP%...
ping -n 2 %DISPLAY_IP% >nul
if %errorlevel%==0 (
    echo [OK] Display is reachable
) else (
    echo [WARNING] Display not reachable
    echo Make sure display is connected and powered on
)

echo.
set /p DISPLAY_NAME="Enter display name (default: Display Principale): "
if "%DISPLAY_NAME%"=="" set DISPLAY_NAME=Display Principale

set /p DISPLAY_LOCATION="Enter location (default: Negozio): "
if "%DISPLAY_LOCATION%"=="" set DISPLAY_LOCATION=Negozio

echo.
pause

REM Step 6: Create Config
cls
echo ======================================
echo   STEP 6/6: Creating Configuration
echo ======================================
echo.

echo Creating config.json...
(
echo {
echo   "display": {
echo     "ip": "%DISPLAY_IP%",
echo     "name": "%DISPLAY_NAME%",
echo     "location": "%DISPLAY_LOCATION%"
echo   },
echo   "schedule": {
echo     "enabled": true,
echo     "power_on": "08:00",
echo     "power_off": "20:00",
echo     "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
echo     "source_on_startup": "hdmi1"
echo   },
echo   "watchdog": {
echo     "enabled": true,
echo     "check_interval": 300,
echo     "max_retry": 3
echo   },
echo   "notifications": {
echo     "telegram": {
echo       "enabled": false,
echo       "bot_token": "",
echo       "chat_id": ""
echo     },
echo     "email": {
echo       "enabled": false,
echo       "smtp_server": "smtp.gmail.com",
echo       "smtp_port": 587,
echo       "username": "",
echo       "password": "",
echo       "to_email": ""
echo     }
echo   },
echo   "security": {
echo     "username": "admin",
echo     "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
echo   }
echo }
) > C:\DisplayControl\config.json

echo [OK] Configuration created
echo.

REM Final Summary
cls
echo ======================================
echo   SETUP COMPLETED!
echo ======================================
echo.
echo Configuration Summary:
echo - Display IP: %DISPLAY_IP%
echo - Display Name: %DISPLAY_NAME%
echo - Location: %DISPLAY_LOCATION%
echo - Default Login: admin / admin123
echo.
echo Next steps:
echo 1. Copy display_system.py to C:\DisplayControl
echo 2. Run: start.bat
echo 3. Access: http://localhost:5000
echo.
echo For remote access:
echo - Get Tailscale IP: tailscale ip -4
echo - Access from anywhere: http://[TAILSCALE_IP]:5000
echo.
echo To install as Windows service:
echo - Run: install_service.bat (as Administrator)
echo.
echo Documentation:
echo - Check setup_guide in the artifacts
echo.
pause
