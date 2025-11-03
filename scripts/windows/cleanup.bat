@echo off
title Log Cleanup
color 06

echo ======================================
echo   LOG CLEANUP
echo ======================================
echo.

REM Elimina log piÃ¹ vecchi di 30 giorni
echo Deleting logs older than 30 days...
forfiles /P "C:\DisplayControl\logs" /M *.log /D -30 /C "cmd /c del @path" 2>nul
if %errorlevel%==0 (
    echo Old logs deleted!
) else (
    echo No old logs found or error occurred
)

echo.

REM Controlla dimensione log corrente
echo Checking current log size...
for %%F in ("C:\DisplayControl\logs\display.log") do set size=%%~zF

if %size% GTR 10485760 (
    echo Log file is large ^(%size% bytes^), rotating...
    
    REM Crea nome file con timestamp
    set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    set timestamp=%timestamp: =0%
    
    move "C:\DisplayControl\logs\display.log" "C:\DisplayControl\logs\display_%timestamp%.log" >nul
    echo. > "C:\DisplayControl\logs\display.log"
    echo Log rotated to: display_%timestamp%.log
) else (
    echo Log size OK ^(%size% bytes^)
)

echo.
echo ======================================
echo Cleanup completed!
echo ======================================
echo.
pause
