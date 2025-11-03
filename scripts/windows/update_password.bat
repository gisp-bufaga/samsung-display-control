@echo off
title Update Admin Password
color 0E

echo ======================================
echo   UPDATE ADMIN PASSWORD
echo ======================================
echo.
echo This tool will help you change
echo the admin password
echo.

set /p NEW_PASSWORD="Enter new password: "

if "%NEW_PASSWORD%"=="" (
    echo Error: Password cannot be empty
    pause
    exit /b 1
)

echo.
echo Generating hash...
python -c "import hashlib; print('New hash:', hashlib.sha256('%NEW_PASSWORD%'.encode()).hexdigest())" > temp_hash.txt

type temp_hash.txt
echo.
echo.
echo Copy the hash above and update it in config.json
echo under security.password_hash
echo.
echo Path: C:\DisplayControl\config.json
echo.

del temp_hash.txt

pause
