@echo off
setlocal EnableExtensions
title ThreadVault Chinese UI Launcher

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "THREADVAULT_URL=http://127.0.0.1:8766/zh"
set "THREADVAULT_READY_MARKER=20260702-paths"

echo.
echo ========================================
echo   ThreadVault Chinese UI Launcher
echo ========================================
echo.
echo URL: %THREADVAULT_URL%
echo.
echo Notes:
echo - If the local service is already running, this opens the Chinese UI.
echo - On first launch, this starts the local service and then opens the browser.
echo - Closing the browser page will stop the service after a few seconds.
echo - If the browser does not open, manually visit the URL above.
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python launcher py.exe was not found.
  echo Install Python 3.12 or add the Python launcher to PATH, then try again.
  goto failed
)

py -3.12 -c "import sys; sys.path.insert(0, 'src'); import threadvault.cli" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python 3.12 could not load ThreadVault.
  echo Make sure this file is in the ThreadVault project folder and dependencies are installed.
  echo.
  py -3.12 -c "import sys; sys.path.insert(0, 'src'); import threadvault.cli"
  goto failed
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$url='%THREADVAULT_URL%'; $marker='%THREADVAULT_READY_MARKER%';" ^
  "$conn=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1;" ^
  "if (-not $conn) { exit 2 }" ^
  "try { $body=(Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2 -Headers @{ 'Cache-Control'='no-cache' }).Content; if ($body -like ('*' + $marker + '*')) { exit 0 } } catch {}" ^
  "try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop; Start-Sleep -Milliseconds 500; exit 1 } catch { exit 3 }" >nul 2>nul
if errorlevel 3 (
  echo [ERROR] Port 8766 is in use, but the running service is stale and could not be stopped.
  echo Close the old ThreadVault window or stop the process using port 8766, then try again.
  goto failed
)
if errorlevel 2 (
  rem No local service is listening; start below.
) else (
  if errorlevel 1 (
    echo Stale local service was stopped. Starting the current Chinese UI...
  ) else (
    echo Current local service is already running. Opening the Chinese UI...
    start "" "%THREADVAULT_URL%"
    goto done
  )
)

echo Starting local Web UI...
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='%THREADVAULT_URL%'; for ($i = 0; $i -lt 40; $i++) { try { Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 1 | Out-Null; Start-Process $u; exit 0 } catch { Start-Sleep -Milliseconds 500 } }; Start-Process $u" >nul 2>nul

py -3.12 -c "import sys; sys.path.insert(0, 'src'); from threadvault.cli import app; app()" ui serve --lang zh --exit-on-close
if errorlevel 1 goto failed

:done
echo.
echo ThreadVault has exited. Press any key to close this window.
pause >nul
exit /b 0

:failed
echo.
echo Startup failed. Press any key to close this window.
pause >nul
exit /b 1
