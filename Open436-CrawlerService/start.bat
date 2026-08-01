@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set CRAWLER_DEPENDENCY_MODE=degraded
echo Starting CrawlerService on port 8009 (degraded mode)...
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8009
