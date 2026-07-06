@echo off
setlocal EnableExtensions
title ThreadVault Desktop Launcher

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"

echo.
echo ========================================
echo   ThreadVault Desktop Launcher
echo ========================================
echo.
echo This starts the native Tkinter desktop app.
echo No browser, web server, Electron, React, or Tauri is required.
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

echo Running desktop smoke check...
py -3.12 -c "import sys; sys.path.insert(0, 'src'); from threadvault.cli import app; app()" desktop smoke --json >nul
if errorlevel 1 (
  echo [ERROR] Desktop smoke check failed.
  echo Run this command for details:
  echo py -3.12 -c "import sys; sys.path.insert(0, 'src'); from threadvault.cli import app; app()" desktop smoke --json
  goto failed
)

echo Starting native desktop app...
py -3.12 -c "import sys; sys.path.insert(0, 'src'); from threadvault.cli import app; app()" desktop launch
if errorlevel 1 goto failed

:done
echo.
echo ThreadVault desktop has exited. Press any key to close this window.
pause >nul
exit /b 0

:failed
echo.
echo Startup failed. Press any key to close this window.
pause >nul
exit /b 1
