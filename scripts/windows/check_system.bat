@echo off
title System Status Check
color 0B

:menu
cls
echo ======================================
echo   DISPLAY CONTROL - STATUS CHECK
echo ======================================
echo.
echo Current Time: %date% %time%
echo.
echo ======================================
echo  SYSTEM CHECKS
echo ======================================
echo.

REM Check 1: Tailscale
echo [1] Tailscale Service...
net start | findstr /C:"Tailscale" >nul
if %errorlevel%==0 (
    echo     Status: RUNNING
    tailscale ip -4 2>nul
    if %errorlevel%==0 (
        echo     IP: 
        tailscale ip -4
    )
) else (
    echo     Status: NOT RUNNING [ERROR]
)

echo.

REM Check 2: Display Control
echo [2] Display Control Server...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr python >nul
if %errorlevel%==0 (
    echo     Status: RUNNING
) else (
    tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | findstr pythonw >nul
    if %errorlevel%==0 (
        echo     Status: RUNNING (background)
    ) else (
        echo     Status: NOT RUNNING [ERROR]
    )
)

echo.

REM Check 3: Display Connectivity
echo [3] Display Connectivity...
ping -n 1 -w 1000 192.168.1.100 >nul 2>&1
if %errorlevel%==0 (
    echo     Status: REACHABLE
    echo     IP: 192.168.1.100
) else (
    echo     Status: UNREACHABLE [ERROR]
)

echo.

REM Check 4: Xibo Player
echo [4] Xibo Player...
tasklist /FI "IMAGENAME eq XiboClient.exe" 2>nul | findstr Xibo >nul
if %errorlevel%==0 (
    echo     Status: RUNNING
) else (
    echo     Status: NOT RUNNING [WARNING]
)

echo.

REM Check 5: System Resources
echo [5] System Resources...
for /f "tokens=2 delims==" %%a in ('wmic cpu get loadpercentage /value') do set cpu=%%a
echo     CPU Usage: %cpu%%%
for /f "tokens=4" %%a in ('systeminfo ^| findstr Physical') do set mem=%%a
echo     Memory Available: %mem%

echo.

REM Check 6: Log File
echo [6] Recent Logs...
if exist C:\DisplayControl\logs\display.log (
    echo     Last 5 log entries:
    powershell -Command "Get-Content C:\DisplayControl\logs\display.log -Tail 5"
) else (
    echo     Log file not found [WARNING]
)

echo.
echo ======================================
echo  ACTIONS
echo ======================================
echo.
echo [R] Refresh Status
echo [S] Start System
echo [T] Stop System
echo [L] View Full Logs
echo [Q] Quit
echo.
choice /C RSTLQ /N /M "Select action: "

if errorlevel 5 goto :end
if errorlevel 4 goto :viewlogs
if errorlevel 3 goto :stopsystem
if errorlevel 2 goto :startsystem
if errorlevel 1 goto :menu

:startsystem
echo.
echo Starting system...
call C:\DisplayControl\start.bat
timeout /t 3 /nobreak >nul
goto :menu

:stopsystem
echo.
echo Stopping system...
call C:\DisplayControl\stop.bat
timeout /t 3 /nobreak >nul
goto :menu

:viewlogs
cls
echo ======================================
echo   SYSTEM LOGS (Last 50 entries)
echo ======================================
echo.
powershell -Command "Get-Content C:\DisplayControl\logs\display.log -Tail 50"
echo.
echo Press any key to return to menu...
pause >nul
goto :menu

:end
exit
