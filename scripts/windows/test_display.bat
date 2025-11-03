@echo off
title Display Connection Test
color 0B

echo ======================================
echo   DISPLAY CONNECTION TEST
echo ======================================
echo.

set DISPLAY_IP=192.168.1.100

echo Testing connection to %DISPLAY_IP%...
echo.

REM Test 1: Ping
echo [1/4] Network ping test...
ping -n 4 %DISPLAY_IP%
if %errorlevel%==0 (
    echo Result: SUCCESS - Display is reachable
) else (
    echo Result: FAILED - Display is not reachable
    echo Check network cable and IP address
)

echo.
echo [2/4] MDC port test (1515)...
powershell -Command "$client = New-Object System.Net.Sockets.TcpClient; try { $client.Connect('%DISPLAY_IP%', 1515); $client.Close(); Write-Host 'Result: SUCCESS - MDC port is open' } catch { Write-Host 'Result: FAILED - MDC port is closed or filtered' }"

echo.
echo [3/4] Python MDC library test...
python -c "from samsung_mdc import MDC; d = MDC('%DISPLAY_IP%'); print('Result: SUCCESS - Library loaded'); print('Status:', d.get_power_status())" 2>nul
if %errorlevel%==0 (
    echo MDC communication OK
) else (
    echo Result: FAILED - Cannot communicate with display
    echo Make sure MDC is enabled on the display
)

echo.
echo [4/4] Display information...
python -c "from samsung_mdc import MDC; d = MDC('%DISPLAY_IP%'); print('Power:', d.get_power_status())" 2>nul

echo.
echo ======================================
echo Test completed!
echo ======================================
echo.
echo If all tests passed, the display is ready
echo If tests failed, check:
echo - Display is powered on
echo - Network cable connected
echo - IP address is correct (%DISPLAY_IP%)
echo - MDC is enabled in display settings
echo.
pause
