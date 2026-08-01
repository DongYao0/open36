#!/bin/bash
# ══════════════════════════════════════════════════
#  Open436 一键启动脚本 (Linux/Mac)
#  使用: chmod +x docker-start.sh && ./docker-start.sh
# ══════════════════════════════════════════════════
set -e

cd "$(dirname "$0")"

# 颜色
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "${C}═════════════════════════════════════════════════════"
echo -e "  Open436 Docker 一键启动器"
echo -e "═════════════════════════════════════════════════════${NC}"
echo ""
echo "  请选择启动模式:"
echo "    1. 本地开发模式 (仅基础设施，应用服务在IDE中运行)"
echo "    2. 全容器化部署 (所有服务都在Docker中运行)"
echo ""
read -p "请输入选择 (1 或 2): " MODE

# 1. 检查 Docker
echo ""
echo -e "${Y}[1/4]${NC} 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${R}  [X] Docker 未安装，请先安装 Docker Desktop${NC}"
    exit 1
fi
if ! docker info &> /dev/null; then
    echo -e "${R}  [X] Docker 未启动，请先启动 Docker Desktop${NC}"
    exit 1
fi
echo -e "${G}  [OK] Docker 就绪${NC}"

# 2. 环境配置
echo -e "${Y}[2/4]${NC} 检查环境配置..."
if [ ! -f .env ]; then
    cp .env.docker .env
    echo -e "${G}  [OK] 已从 .env.docker 创建 .env${NC}"
else
    echo -e "${G}  [OK] .env 已存在${NC}"
fi

# 3. 启动服务
if [ "$MODE" = "1" ]; then
    echo ""
    echo -e "${Y}[3/4]${NC} 启动基础设施..."
    docker compose up -d
    echo ""
    echo -e "${Y}[4/4]${NC} 配置 Kong 路由到宿主机..."
    bash deploy/dev/kong-config.sh 2>/dev/null || echo -e "${Y}  [!] Kong 配置失败，可手动执行: bash deploy/dev/kong-config.sh${NC}"
    echo ""
    echo -e "${C}═════════════════════════════════════════════════════"
    echo -e "  基础设施已启动!"
    echo -e "═════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${G}请在 IDE 中启动应用服务:${NC}"
    echo "    Auth:       8081"
    echo "    Enrollment: 8084"
    echo "    Forum:      8003"
    echo "    File:       8007"
    echo "    AI:         8008"
    echo ""
    echo -e "  ${G}基础设施:${NC}"
    echo "    PostgreSQL: localhost:55400  (open436/open436)"
    echo "    Redis:      localhost:6380"
    echo "    Consul:     http://localhost:8500"
    echo "    Minio:      http://localhost:9001  (minioadmin/minioadmin)"
    echo "    Kong Proxy: http://localhost:8000"
    echo "    Kong Admin: http://localhost:8001"
    echo ""
elif [ "$MODE" = "2" ]; then
    PROFILE=""
    if [ "${1:-}" = "--with-hoj" ] || [ "${1:-}" = "--hoj" ]; then
        PROFILE="--profile hoj"
        echo -e "${C}  包含 HOJ 在线判题系统${NC}"
    fi
    echo ""
    echo -e "${Y}[3/4]${NC} 构建并启动所有服务 (首次较慢, 请耐心等待)..."
    docker compose -f docker-compose.full.yml $PROFILE up -d --build 2>&1 | tail -5
    echo ""
    echo -e "${Y}[4/4]${NC} 等待核心服务就绪 (30s)..."
    sleep 15
    echo -n "  ."
    sleep 15
    echo " done"
    echo "  配置 Kong 路由..."
    bash docker/init-kong.sh 2>/dev/null || echo -e "${Y}  [!] Kong 配置失败，可手动执行: bash docker/init-kong.sh${NC}"
    echo ""
    echo -e "${C}═════════════════════════════════════════════════════"
    echo -e "  所有服务已启动!"
    echo -e "═════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${G}前端:${NC}"
    echo "    用户端:    http://localhost:3000"
    echo "    管理后台:  http://localhost:3001"
    echo ""
    echo -e "  ${G}基础设施:${NC}"
    echo "    PostgreSQL: localhost:55400  (open436/open436)"
    echo "    Redis:      localhost:6380"
    echo "    Consul:     http://localhost:8500"
    echo "    Minio:      http://localhost:9001  (minioadmin/minioadmin)"
    echo "    Kong Proxy: http://localhost:8000"
    echo "    Kong Admin: http://localhost:8001"
    echo ""
    echo -e "  ${G}后端服务 (通过 Kong 访问):${NC}"
    echo "    Auth:       http://localhost:8000/api/auth"
    echo "    Enrollment: http://localhost:8000/api/enrollment"
    echo "    Interview:  http://localhost:8000/api/interview"
    echo ""
else
    echo ""
    echo -e "${R}  [X] 无效选择，请输入 1 或 2${NC}"
    exit 1
fi

echo -e "  ${Y}提示:${NC}"
echo "    查看日志: docker compose logs -f [服务名]"
echo "    停止服务: docker compose down"
echo "    含HOJ启动: ./docker-start.sh --with-hoj"
echo ""
