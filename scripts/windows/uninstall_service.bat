@echo off
title Uninstall Windows Service
color 0C

echo ======================================
echo   REMOVE WINDOWS SERVICE
echo ======================================
echo.

REM Verifica privilegi admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges!
    pause
    exit /b 1
)

echo WARNING: This will remove the Display Control service
echo.
choice /C YN /M "Continue with removal?"

if errorlevel 2 goto :cancel

echo.
echo Stopping service...
nssm stop DisplayControl

timeout /t 3 /nobreak >nul

echo Removing service...
nssm remove DisplayControl confirm

echo.
echo ======================================
echo Service removed successfully!
echo ======================================
echo.
pause
exit /b 0

:cancel
echo.
echo Operation cancelled
pause
exit /b 0
