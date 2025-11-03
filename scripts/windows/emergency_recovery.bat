@echo off
title Emergency Recovery
color 0C

echo ======================================
echo   EMERGENCY RECOVERY PROCEDURE
echo ======================================
echo.
echo This script will attempt to recover
echo the display and system from errors
echo.
pause

echo.
echo [1/7] Stopping current services...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 3 /nobreak >nul
echo Done!

echo.
echo [2/7] Restarting Tailscale...
net stop Tailscale >nul 2>&1
timeout /t 2 /nobreak >nul
net start Tailscale >nul 2>&1
timeout /t 5 /nobreak >nul
echo Done!

echo.
echo [3/7] Testing display connection...
ping -n 1 192.168.1.100 >nul 2>&1
if %errorlevel%==0 (
    echo Display reachable!
) else (
    echo WARNING: Display not reachable
    echo Check network connection
)

echo.
echo [4/7] Attempting display power cycle...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.power(False)" 2>nul
timeout /t 10 /nobreak >nul
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.power(True)" 2>nul
timeout /t 15 /nobreak >nul
echo Done!

echo.
echo [5/7] Setting source to HDMI1...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.source('hdmi1')" 2>nul
echo Done!

echo.
echo [6/7] Checking Xibo Player...
tasklist /FI "IMAGENAME eq XiboClient.exe" 2>nul | findstr Xibo >nul
if %errorlevel%==0 (
    echo Xibo is running
) else (
    echo Xibo not running, attempting restart...
    start "" "C:\Program Files\Xibo Player\XiboClient.exe" 2>nul
    timeout /t 5 /nobreak >nul
)

echo.
echo [7/7] Restarting Display Control...
cd C:\DisplayControl
start /B pythonw display_system.py
timeout /t 5 /nobreak >nul
echo Done!

echo.
echo ======================================
echo Recovery procedure completed!
echo ======================================
echo.
echo Please check:
echo 1. Dashboard accessible at http://localhost:5000
echo 2. Display is powered on
echo 3. Xibo Player is running
echo.
echo If problems persist, check logs:
echo   view_logs.bat
echo.
pause
