@echo off
title Display Control - Restart
color 0E

echo ======================================
echo Display Control System - Restarting
echo ======================================
echo.

echo Stopping current instance...
call C:\DisplayControl\stop.bat

echo.
echo Starting new instance...
timeout /t 3 /nobreak >nul
call C:\DisplayControl\start.bat
