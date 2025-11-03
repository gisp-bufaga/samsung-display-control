@echo off
title Backup Configuration
color 0D

echo ======================================
echo   CONFIGURATION BACKUP
echo ======================================
echo.

REM Crea directory backup con data
set BACKUP_DIR=C:\DisplayControl\backups\%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%

echo Creating backup directory...
mkdir "%BACKUP_DIR%" >nul 2>&1

echo.
echo Backing up files...

REM Backup files
if exist C:\DisplayControl\display_system.py (
    copy C:\DisplayControl\display_system.py "%BACKUP_DIR%\" >nul
    echo - display_system.py [OK]
)

if exist C:\DisplayControl\config.json (
    copy C:\DisplayControl\config.json "%BACKUP_DIR%\" >nul
    echo - config.json [OK]
)

if exist C:\DisplayControl\*.bat (
    copy C:\DisplayControl\*.bat "%BACKUP_DIR%\" >nul
    echo - batch scripts [OK]
)

REM Backup logs
if exist C:\DisplayControl\logs\display.log (
    copy C:\DisplayControl\logs\display.log "%BACKUP_DIR%\display.log" >nul
    echo - display.log [OK]
)

echo.
echo ======================================
echo Backup completed successfully!
echo ======================================
echo.
echo Location: %BACKUP_DIR%
echo.

REM Elimina backup piÃ¹ vecchi di 30 giorni
echo Cleaning old backups (older than 30 days)...
forfiles /P "C:\DisplayControl\backups" /D -30 /C "cmd /c if @isdir==TRUE rmdir /S /Q @path" >nul 2>&1
echo Old backups cleaned!

echo.
pause
