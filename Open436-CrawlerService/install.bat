@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Open436 CrawlerService Install
echo ========================================
echo.

REM 1. Create venv
echo [1/3] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo     Done.
) else (
    echo     Already exists, skipping.
)

REM 2. Install deps (skip browser download)
echo.
echo [2/3] Installing dependencies (aliyun mirror)...
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
set PATCHRIGHT_SKIP_BROWSER_DOWNLOAD=1
call .venv\Scripts\pip.exe install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
if errorlevel 1 (
    echo     FAILED!
    pause
    exit /b 1
)
echo     Done.

REM 3. Install Playwright browser (via proxy)
echo.
echo [3/3] Installing Playwright browser (proxy: 127.0.0.1:7897)...
set HTTPS_PROXY=http://127.0.0.1:7897
set HTTP_PROXY=http://127.0.0.1:7897
call .venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 (
    echo     FAILED! Make sure proxy is running on 127.0.0.1:7897
    pause
    exit /b 1
)
echo     Done.

REM 4. Create data dir
if not exist "data" mkdir data

echo.
echo ========================================
echo   Install complete! Start: start.bat
echo ========================================
echo.
pause
