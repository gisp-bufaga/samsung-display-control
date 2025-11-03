@echo off
title Install Windows Service
color 0E

echo ======================================
echo   WINDOWS SERVICE INSTALLATION
echo ======================================
echo.

REM Verifica privilegi admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges!
    echo Right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Download NSSM se non presente
if not exist "C:\DisplayControl\nssm.exe" (
    echo NSSM not found, downloading...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'C:\DisplayControl\nssm.zip'"
    powershell -Command "Expand-Archive -Path 'C:\DisplayControl\nssm.zip' -DestinationPath 'C:\DisplayControl' -Force"
    copy "C:\DisplayControl\nssm-2.24\win64\nssm.exe" "C:\DisplayControl\nssm.exe" >nul
    echo NSSM downloaded successfully!
    echo.
)

REM Trova Python
for /f "tokens=*" %%a in ('where python 2^>nul') do set PYTHON_PATH=%%a

if "%PYTHON_PATH%"=="" (
    echo ERROR: Python not found in PATH!
    echo Install Python and try again
    pause
    exit /b 1
)

echo Python found at: %PYTHON_PATH%
echo.

REM Installa servizio
echo Installing service...
cd C:\DisplayControl
nssm install DisplayControl "%PYTHON_PATH%" "C:\DisplayControl\display_system.py"
nssm set DisplayControl AppDirectory "C:\DisplayControl"
nssm set DisplayControl DisplayName "Display Control System"
nssm set DisplayControl Description "Sistema di controllo remoto display Samsung con scheduling e watchdog"
nssm set DisplayControl Start SERVICE_AUTO_START
nssm set DisplayControl AppStdout "C:\DisplayControl\logs\service_output.log"
nssm set DisplayControl AppStderr "C:\DisplayControl\logs\service_error.log"

echo.
echo Starting service...
nssm start DisplayControl

timeout /t 3 /nobreak >nul

echo.
echo ======================================
echo Service installed successfully!
echo ======================================
echo.
echo Service Name: DisplayControl
echo Status: 
nssm status DisplayControl
echo.
echo Manage service with:
echo - Start:   nssm start DisplayControl
echo - Stop:    nssm stop DisplayControl
echo - Restart: nssm restart DisplayControl
echo - Remove:  nssm remove DisplayControl confirm
echo.
pause
