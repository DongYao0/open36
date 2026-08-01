@echo off
chcp 65001 >nul 2>nul
title Open436 Docker 一键启动器
color 0A

echo.
echo  ═══════════════════════════════════════════════════
echo       Open436 Docker 一键启动器
echo  ═══════════════════════════════════════════════════
echo.
echo  请选择启动模式:
echo    1. 本地开发模式 (仅基础设施，应用服务在IDE中运行)
echo    2. 全容器化部署 (所有服务都在Docker中运行)
echo.
set /p mode="请输入选择 (1 或 2): "

set "ROOT=%~dp0"
cd /d "%ROOT%"

REM [1/4] 检查 Docker
echo.
echo [1/4] 检查 Docker...
where docker >nul 2>nul || (
    echo   [X] Docker 未安装，请先安装 Docker Desktop
    pause & exit /b 1
)
docker info >nul 2>nul || (
    echo   [X] Docker 未启动，请先启动 Docker Desktop
    pause & exit /b 1
)
echo   [OK] Docker 就绪

REM [2/4] 环境配置
echo [2/4] 检查环境配置...
if not exist .env (
    copy .env.docker .env >nul
    echo   [OK] 已从 .env.docker 创建 .env
) else (
    echo   [OK] .env 已存在
)

REM [3/4] 启动服务
if "%mode%"=="1" (
    echo.
    echo [3/4] 启动基础设施...
    docker compose up -d
    echo.
    echo [4/4] 配置 Kong 路由到宿主机...
    bash deploy\dev\kong-config.sh 2>nul || echo   [!] Kong 配置需手动执行: bash deploy\dev\kong-config.sh
    echo.
    echo  ═══════════════════════════════════════════════════
    echo       基础设施已启动!
    echo  ═══════════════════════════════════════════════════
    echo.
    echo   请在 IDE 中启动应用服务:
    echo     Auth:       8081
    echo     Enrollment: 8084
    echo     Forum:      8003
    echo     File:       8007
    echo     AI:         8008
    echo.
    echo   基础设施:
    echo     PostgreSQL: localhost:55400  (open436/open436)
    echo     Redis:      localhost:6380
    echo     Consul:     http://localhost:8500
    echo     Minio:      http://localhost:9001  (minioadmin/minioadmin)
    echo     Kong Proxy: http://localhost:8000
    echo     Kong Admin: http://localhost:8001
    echo.
) else if "%mode%"=="2" (
    echo.
    echo [3/4] 构建并启动所有服务 (首次较慢, 请耐心等待)...
    if "%1"=="--with-hoj" (
        echo   包含 HOJ 在线判题系统
        docker compose -f docker-compose.full.yml --profile hoj up -d --build
    ) else (
        docker compose -f docker-compose.full.yml up -d --build
    )
    echo.
    echo [4/4] 等待核心服务就绪 (30s^)...
    timeout /t 30 /nobreak >nul
    echo   配置 Kong 路由...
    bash docker\init-kong.sh 2>nul || echo   [!] Kong 配置需手动执行
    echo.
    echo  ═══════════════════════════════════════════════════
    echo       所有服务已启动!
    echo  ═══════════════════════════════════════════════════
    echo.
    echo   前端:
    echo     用户端:    http://localhost:3000
    echo     管理后台:  http://localhost:3001
    echo.
    echo   基础设施:
    echo     PostgreSQL: localhost:55400  (open436/open436)
    echo     Redis:      localhost:6380
    echo     Consul:     http://localhost:8500
    echo     Minio:      http://localhost:9001  (minioadmin/minioadmin)
    echo     Kong Proxy: http://localhost:8000
    echo     Kong Admin: http://localhost:8001
    echo.
    echo   后端服务 (通过 Kong 访问):
    echo     Auth:       http://localhost:8000/api/auth
    echo     Enrollment: http://localhost:8000/api/enrollment
    echo     Interview:  http://localhost:8000/api/interview
    echo.
) else (
    echo.
    echo  [X] 无效选择，请输入 1 或 2
    pause
    exit /b 1
)

echo   常用命令:
echo     查看日志: docker compose logs -f [服务名]
echo     停止服务: docker compose down
echo     含HOJ启动: docker-start.bat --with-hoj
echo.
pause
