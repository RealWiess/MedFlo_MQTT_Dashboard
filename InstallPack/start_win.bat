@echo off
setlocal
cd /d "%~dp0"

:: --- 1. Kill only the process holding port 8080 (not the scanner) ---
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080.*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
ping 127.0.0.1 -n 2 >nul

:: --- 2. Start server.py in a separate background window ---
start "MedFlow-Server" /min cmd /c "python server.py --no-browser"

:: --- 3. Wait until server actually responds (max ~15 seconds) ---
set /a tries=0
:WAIT_LOOP
ping 127.0.0.1 -n 2 >nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/',timeout=1)" >nul 2>&1
if %errorlevel% equ 0 goto OPEN_BROWSER
set /a tries=%tries%+1
if %tries% lss 8 goto WAIT_LOOP
echo Server may not have started. Opening anyway...

:OPEN_BROWSER
:: --- 4. Open default browser ---
start http://127.0.0.1:8080/

endlocal
