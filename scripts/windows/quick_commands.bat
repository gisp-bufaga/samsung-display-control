@echo off
title Quick Commands
color 0B

:menu
cls
echo ======================================
echo   QUICK COMMANDS MENU
echo ======================================
echo.
echo Current Time: %date% %time%
echo.
echo ======================================
echo   DISPLAY COMMANDS
echo ======================================
echo.
echo [1] Power ON
echo [2] Power OFF
echo [3] Check Status
echo [4] Set Source - HDMI 1
echo [5] Set Source - HDMI 2
echo [6] Set Source - DisplayPort
echo.
echo ======================================
echo   SYSTEM COMMANDS
echo ======================================
echo.
echo [7] Restart Xibo Player
echo [8] View System Status
echo [9] View Live Logs
echo.
echo ======================================
echo   ACTIONS
echo ======================================
echo.
echo [0] Exit
echo.
choice /C 1234567890 /N /M "Select option: "

if errorlevel 10 goto :end
if errorlevel 9 goto :viewlogs
if errorlevel 8 goto :systemstatus
if errorlevel 7 goto :restartxibo
if errorlevel 6 goto :sourcedp
if errorlevel 5 goto :sourcehdmi2
if errorlevel 4 goto :sourcehdmi1
if errorlevel 3 goto :checkstatus
if errorlevel 2 goto :poweroff
if errorlevel 1 goto :poweron

:poweron
echo.
echo Sending Power ON command...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.power(True); print('Display powered ON')"
echo.
pause
goto :menu

:poweroff
echo.
echo Sending Power OFF command...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.power(False); print('Display powered OFF')"
echo.
pause
goto :menu

:checkstatus
echo.
echo Checking display status...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); print('Power Status:', d.get_power_status())"
echo.
pause
goto :menu

:sourcehdmi1
echo.
echo Setting source to HDMI 1...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.source('hdmi1'); print('Source changed to HDMI 1')"
echo.
pause
goto :menu

:sourcehdmi2
echo.
echo Setting source to HDMI 2...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.source('hdmi2'); print('Source changed to HDMI 2')"
echo.
pause
goto :menu

:sourcedp
echo.
echo Setting source to DisplayPort...
python -c "from samsung_mdc import MDC; d = MDC('192.168.1.100'); d.source('displayport'); print('Source changed to DisplayPort')"
echo.
pause
goto :menu

:restartxibo
echo.
echo Restarting Xibo Player...
taskkill /F /IM XiboClient.exe >nul 2>&1
timeout /t 3 /nobreak >nul
start "" "C:\Program Files\Xibo Player\XiboClient.exe" 2>nul
echo Xibo Player restarted
echo.
pause
goto :menu

:systemstatus
echo.
call C:\DisplayControl\check_system.bat
goto :menu

:viewlogs
echo.
call C:\DisplayControl\view_logs.bat
goto :menu

:end
exit
