@echo off
title Display Control - Shutdown
color 0C

echo ======================================
echo Display Control System - Stopping
echo ======================================
echo.

echo Stopping Display Control...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq display_system*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

timeout /t 2 /nobreak >nul

echo.
echo System stopped!
echo.
pause
