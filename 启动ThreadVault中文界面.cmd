@echo off
setlocal
title ThreadVault 中文界面启动器

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"

echo.
echo ========================================
echo   ThreadVault 中文界面启动器
echo ========================================
echo.
echo 正在启动本地 Web UI...
echo 地址: http://127.0.0.1:8766/zh
echo.
echo 提示:
echo - 浏览器会自动打开中文界面。
echo - 关闭浏览器页面后，服务会自动退出。
echo - 如果没有自动打开，请手动访问上面的地址。
echo.

py -3.12 -c "import sys; sys.path.insert(0, 'src'); from threadvault.cli import app; app()" ui serve --lang zh --open --exit-on-close

echo.
echo ThreadVault 已退出。按任意键关闭窗口。
pause >nul
