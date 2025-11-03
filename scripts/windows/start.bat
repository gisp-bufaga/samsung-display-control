@echo off
title Display Control - Startup
color 0A

echo ======================================
echo Display Control System - Starting
echo ======================================
echo.

echo [1/3] Starting Tailscale...
net start Tailscale >nul 2>&1
if %errorlevel%==0 (
    echo OK: Tailscale started
) else (
    echo WARNING: Tailscale already running or error
)

timeout /t 10 /nobreak >nul

echo.
echo [2/3] Waiting for network...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting Display Control System...
cd C:\DisplayControl
start /B pythonw display_system.py

echo.
echo ======================================
echo System Started Successfully!
echo ======================================
echo.
echo Access dashboard at:
echo - Local: http://localhost:5000
echo - Remote: http://[TAILSCALE_IP]:5000
echo.
echo Press any key to close this window...
pause >nul