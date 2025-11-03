@echo off
title Display Control - Live Logs
color 0A

echo ======================================
echo   LIVE LOG VIEWER
echo ======================================
echo.
echo Showing last 20 lines, then live updates...
echo Press Ctrl+C to stop
echo.
echo ======================================
echo.

powershell -Command "Get-Content C:\DisplayControl\logs\display.log -Wait -Tail 20"
