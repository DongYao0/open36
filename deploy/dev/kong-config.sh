#!/bin/bash
# Kong 开发环境配置脚本（deploy/dev）
# 配置 Kong 路由到宿主机运行的服务

set -euo pipefail

KONG_ADMIN="http://localhost:8001"

# Windows/Mac Docker Desktop 使用 host.docker.internal；Linux 可改为 172.17.0.1
HOST_ADDR="host.docker.internal"

echo "========================================="
echo "Configuring Kong for Development Mode"
echo "========================================="
echo ""
echo "Backend services running on host: ${HOST_ADDR}"
echo ""

# 等待 Kong 就绪
echo "Waiting for Kong to be ready..."
until curl -s http://localhost:8001/status > /dev/null 2>&1; do
    echo "Kong is not ready yet, waiting..."
    sleep 2
done
echo "Kong is ready!"
echo ""

# 显式全量清理（按外键依赖顺序：routes → plugins → services），保证脚本真正幂等
# 旧版仅按名字 DELETE services，当级联失败时 routes/plugins 残留，重复执行即累积重复路由
echo "Cleaning up existing configurations (full purge)..."
for id in $(curl -s $KONG_ADMIN/routes   2>/dev/null | grep -oE '"id":"[^"]*"'   | sed 's/.*"id":"//;s/"//'); do curl -s -o /dev/null -X DELETE $KONG_ADMIN/routes/$id   || true; done
for id in $(curl -s $KONG_ADMIN/plugins  2>/dev/null | grep -oE '"id":"[^"]*"'   | sed 's/.*"id":"//;s/"//'); do curl -s -o /dev/null -X DELETE $KONG_ADMIN/plugins/$id  || true; done
for n  in $(curl -s $KONG_ADMIN/services 2>/dev/null | grep -oE '"name":"[^"]*"' | sed 's/.*"name":"//;s/"//'); do curl -s -o /dev/null -X DELETE $KONG_ADMIN/services/$n || true; done
sleep 1

# 1. 创建 M1 认证服务
echo "Step 1: Creating auth-service..."
curl -i -X POST $KONG_ADMIN/services \
  --data name=auth-service \
  --data url=http://${HOST_ADDR}:8081

echo ""
echo "Creating route for auth-service..."
curl -i -X POST $KONG_ADMIN/services/auth-service/routes \
  --data "paths[]=/api/auth" \
  --data "paths[]=/api/users" \
  --data strip_path=false

echo ""
echo ""

# 2. 创建 M7 文件服务
echo "Step 2: Creating file-service..."
curl -i -X POST $KONG_ADMIN/services \
  --data name=file-service \
  --data url=http://${HOST_ADDR}:8007

echo ""
echo "Creating route for file-service..."
curl -i -X POST $KONG_ADMIN/services/file-service/routes \
  --data "paths[]=/api/files" \
  --data strip_path=false

echo ""
echo ""

# 3. 启用 Sa-Token 认证插件（文件服务需要鉴权）
echo "Step 3: Enabling satoken-auth plugin for file-service..."
curl -i -X POST $KONG_ADMIN/services/file-service/plugins \
  --data name=satoken-auth \
  --data config.auth_service_url=http://${HOST_ADDR}:8081

echo ""
echo ""

# 4. 创建报名服务
echo "Step 4: Creating enrollment-service..."
curl -i -X POST $KONG_ADMIN/services \
  --data name=enrollment-service \
  --data url=http://${HOST_ADDR}:8084

echo ""
echo "Creating route for enrollment-service..."
curl -i -X POST $KONG_ADMIN/services/enrollment-service/routes \
  --data "paths[]=/api/enrollment" \
  --data "paths[]=/api/interview" \
  --data strip_path=false

echo ""
echo ""

# 5. 创建论坛服务（合并 Content + Comment + Section）
echo "Step 5: Creating forum-service..."
curl -i -X POST $KONG_ADMIN/services \
  --data name=forum-service \
  --data url=http://${HOST_ADDR}:8003

echo ""
echo "Creating routes for forum-service..."
curl -i -X POST $KONG_ADMIN/services/forum-service/routes \
  --data "paths[]=/api/posts" \
  --data "paths[]=/api/comments" \
  --data "paths[]=/api/sections" \
  --data "paths[]=/api/replies" \
  --data "paths[]=/api/favorites" \
  --data "paths[]=/api/topics" \
  --data "paths[]=/api/follows" \
  --data strip_path=false

echo ""
echo ""
echo "========================================="
echo "Kong Configuration Complete!"
echo "========================================="
echo ""
echo "Services registered:"
echo "  - auth-service:       http://${HOST_ADDR}:8081 → /api/auth/*, /api/users/*"
echo "  - file-service:       http://${HOST_ADDR}:8007 → /api/files/*"
echo "  - enrollment-service: http://${HOST_ADDR}:8084 → /api/enrollment/*"
echo "  - forum-service:      http://${HOST_ADDR}:8003 → /api/posts/*, /api/comments/*, /api/sections/*, /api/replies/*, /api/topics/*"
echo ""
echo "Verification:"
echo "  - Kong Admin API: curl http://localhost:8001/services"
echo "  - Kong Routes:    curl http://localhost:8001/routes"
echo ""
echo "Test login through Kong:"
echo "  curl -X POST http://localhost:8000/api/auth/login \\\n+    -H 'Content-Type: application/json' \\\n+    -d '{"username":"alice","password":"password123"}'"
echo ""


