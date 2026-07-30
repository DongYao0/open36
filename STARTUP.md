# Open436 启动指南

## 两种启动模式

### 模式1：本地开发（推荐）

基础设施在 Docker 中运行，应用服务在 IDE 中运行。

**启动步骤：**

```bash
# 0. 安装 Python 依赖（首次或依赖变更时）
# 项目使用统一的项目根 .venv（含 Django/FastAPI/uvicorn/langchain 等全部依赖，Forum 与 AIService 共用，无独立 venv）
python -m venv .venv                                  # 仅首次创建
source .venv/bin/activate                             # Windows: .venv\Scripts\activate
pip install -r Open436-AIService/requirements.txt
pip install -r Open436-Forum/requirements.txt
pip install python-multipart                          # AI Service 处理表单/文件上传所需

# 1. 启动基础设施 + FileService（数据库、缓存、Kong、文件服务等）
docker compose up -d

# 2. 验证 Kong 是否启动（有时需要手动启动）
docker compose ps | grep kong
# 如果 kong 未运行，执行：
docker compose up -d kong

# 3. 启动 HOJ 判题系统（可选，需要显式指定 profile）
docker compose --profile hoj up -d

# 4. 在 IDE 中启动应用服务
#    - Auth 服务 (8081) — 认证 + 用户管理
#    - Enrollment 服务 (8084) — 报名管理
#    - Forum 服务 (8003) — 帖子 + 评论 + 板块
#    - AI Service (8008) — AI 智能服务

# 5. 配置 Kong 路由
bash deploy/dev/kong-config.sh
```

**访问地址：**
- 用户前端: http://localhost:3000
- 管理后台: http://localhost:3001
- Kong 代理: http://localhost:8000
- Kong 管理: http://localhost:8001

---

### 模式2：全容器化部署

所有服务都在 Docker 中运行。

**启动步骤：**

```bash
# 启动所有服务（首次较慢，需要构建镜像）
docker compose -f docker-compose.full.yml up -d --build

# 含 HOJ 在线判题系统
docker compose -f docker-compose.full.yml --profile hoj up -d --build

# 配置 Kong 路由
bash docker/init-kong.sh
```

**访问地址：**
- 用户前端: http://localhost:3000
- 管理后台: http://localhost:3001
- Kong 代理: http://localhost:8000
- Kong 管理: http://localhost:8001

---

## HOJ 在线判题系统（可选）

HOJ 相关服务使用 Docker Compose 的 `profiles` 机制，**不会被 `docker compose up -d` 默认启动**。

### 启动 HOJ

```bash
# 启动 HOJ 全套服务（go-judge + hoj-mysql + hoj-backend + hoj-judge + hoj-vue）
docker compose --profile hoj up -d

# 首次启动需要构建镜像（较慢）
docker compose --profile hoj up -d --build
```

### HOJ 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| go-judge | 5050 | 判题沙箱 |
| hoj-mysql | 3308 | HOJ 专用 MySQL |
| hoj-backend | 6688 | HOJ 后端 API |
| hoj-judge | 8088 | 判题服务 |
| hoj-vue | 8066 | HOJ 前端 |

### 验证 HOJ 状态

```bash
docker compose --profile hoj ps
curl -s http://localhost:6688/api/get-website-config  # hoj-backend
curl -s http://localhost:8066/                         # hoj-vue
```

---

## 基础设施端口

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 55400 | 主数据库 |
| Redis | 6380 | 缓存 + Sa-Token Session |
| Consul | 8500 | 服务注册中心 |
| MinIO | 9000/9001 | 对象存储 |
| Kong | 8000/8001 | API 网关 |
| Milvus | 19530 | 向量数据库 |
| FileService | 8007 | 文件服务 (Rust) |

## 业务服务端口

| 服务 | 端口 | 语言/框架 | 说明 |
|------|------|-----------|------|
| Auth | 8081 | Java Spring Boot | 认证服务 |
| Enrollment | 8084 | Java Spring Boot | 报名服务 |
| Forum | 8003 | Django | 论坛服务 |
| AI Service | 8008 | FastAPI | AI 智能服务 |

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f [服务名]

# 停止服务
docker compose down

# 重新构建并启动
docker compose up -d --build
```

## 故障排除

### 0. FileService DNS 解析失败

**现象**：FileService 容器反复重启，日志报 `Failed to create database pool: Io(Custom { kind: Uncategorized, error: "failed to lookup address information: Name or service not known" })`

**原因**：Docker 网络 DNS 同步延迟，file-service 启动时无法解析 `postgres` 主机名

**解决**：
```bash
# 重建 FileService 容器
docker compose up -d --force-recreate file-service
```

### 1. Redis 连接失败

**现象**：Java 服务报 `Unable to connect to Redis`

**原因**：Redis 端口配置错误

**解决**：确保 `application-dev.yml` 中 Redis 端口为 6380

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6380
```

### 2. Kong 启动失败

**现象**：Kong 容器状态为 `Exited(1)` 或 `docker compose ps` 中看不到 kong 容器

**原因**：
- Kong-db 未就绪时 Kong 尝试连接
- kong-migration 的 `restart: on-failure` 可能阻塞 kong 启动
- 之前的容器状态残留影响启动顺序

**解决**：
```bash
# 方案1：重启 Kong
docker compose restart kong

# 方案2：强制重建 Kong 及其依赖
docker compose up -d --force-recreate kong-db kong-migration kong

# 方案3：单独启动 Kong（如果其他服务已运行）
docker compose up -d kong
```

### 2.1 Python 服务启动报错 `Form data requires "python-multipart"`

**现象**：AI Service 启动时报 `RuntimeError: Form data requires "python-multipart" to be installed`

**原因**：FastAPI 处理表单数据（文件上传、`Form(...)` 参数）需要 `python-multipart` 包，但 requirements.txt 中未包含

**解决**：
```bash
pip install python-multipart
# 然后重启 AI Service
```

### 3. Milvus 健康检查失败

**现象**：`docker compose ps` 显示 milvus-standalone 为 `unhealthy`

**原因**：健康检查端点路径配置问题

**影响**：服务实际可用，可忽略

### 4. Auth 服务 Schema 验证失败

**现象**：启动时报 `Schema-validation: wrong column type`

**解决**：将 `ddl-auto` 设置为 `update`

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: update
```

### 5. FileService 构建失败

**现象**：Docker 构建时报 `DATABASE_URL` 错误

**解决**：Dockerfile 中已添加 `ENV DATABASE_URL`，重新构建即可

```bash
docker compose -f docker-compose.full.yml build file-service
docker compose -f docker-compose.full.yml up -d file-service
```

### 6. Forum 接口报 `column xxx does not exist`（500）

**现象**：`GET /api/posts/` 等 Forum 接口返回 500，日志报 `ProgrammingError: column posts.summary does not exist`

**原因**：Forum 数据库 schema 由 `db-init/` SQL 脚本管理，**不是 Django 迁移**（`django_migrations` 表对 content/comment/section 为空，`showmigrations` 永远显示 `[ ]` 属正常现象）。模型新增字段后若只改 `models.py`、不同步 `db-init/` SQL，DB 就缺列。

**解决**（直接改 SQL，**勿用** `python manage.py migrate`，会因"表已存在"失败）：

```bash
# 1. 对 live DB 加列（幂等）
docker exec open436-postgres psql -U open436 -d open436 \
  -c "ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS summary VARCHAR(300);"
# 2. 同步 db-init/ SQL 以便重建库仍生效（新增 db-init/V{N}__add_xxx.sql）
```

### 7. 首页跳转到 3000 而非 5173

**现象**：重启 Vue dev server 后浏览器自动打开 `localhost:3000/app/`，跳转到空白页（而非 3D Landing 首页 `localhost:5173/`）。

**原因**：`Open436-Frontend/vite.config.js` 曾设 `open: true`，但 **:5173 (Landing)** 才是聚合入口。Vue (:3000) 不该自动打开浏览器——它只是被 Landing 代理的后端子应用。Vue Router 在 `/` 路径会执行 `window.location.href='/'` 跳回 Landing 根，但 3000 端口上没有 Landing。

**解决**：已修复（2026-07-30），无需手动干预：
- `Open436-Frontend/vite.config.js`: `open: true` → `open: false`
- `Open436-Landing/vite.config.js`: 已添加 `open: true`

**正确启动顺序**：
```bash
# 先启 Vue（静默，不打开浏览器）
cd Open436-Frontend && npm run dev    # :3000, open:false

# 后启 Landing（自动打开浏览器到 :5173）
cd Open436-Landing && npm run dev     # :5173, open:true
```

### 8. AI Service 启动失败合集

#### 8.1 缺少 `langchain-openai`

**现象**：`ModuleNotFoundError: No module named 'langchain_openai'`

**原因**：`requirements.txt` 未包含此依赖

**解决**：
```bash
pip install langchain-openai
# 警告 langgraph-prebuilt 与 langchain-core 版本冲突可忽略，不影响运行
```

#### 8.2 端口 0.0.0.0:8008 绑定失败（WinError 10048）

**现象**：`[winerror 10048] error while attempting to bind on address ('0.0.0.0', 8008)`

**原因**：Windows 端口保留或旧进程残留（非 Docker 容器原因，`open436-ai-service` 容器早已停止）

**解决**：改用 `127.0.0.1` 绑定，开发环境仅需本地访问：
```bash
cd Open436-AIService
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

### 9. Kong 路由 host 指向旧 IP 导致 502

**现象**：`curl http://localhost:8000/api/auth/register` 返回 502，直连 `:8081` 正常

**原因**：`kong-config.sh` 重复执行产生多条路由，旧路由 host 为 `192.168.50.97`（已失效的旧开发机 IP）

**解决**：
```bash
# 修复 auth-service 上游地址
curl -X PATCH http://localhost:8001/services/auth-service \
  --data host=host.docker.internal --data port=8081
```

### 10. 算法平台显示错误 / HOJ MySQL 不自动重启

**现象**：访问算法平台 `/algo/` 显示错误，`hoj-backend` 日志报 `CommunicationsLinkFailure: UnknownHostException: hoj-mysql`。

**直接原因**：`hoj-mysql` 容器 Exited 后没有自动重启，backend 连不上 MySQL。

**深层根因**（2026-07-30 修复）：
`docker-compose.yml` 中 **只有 `hoj-mysql` 缺少 `restart` 策略**，其他所有 HOJ 容器（go-judge / hoj-backend / hoj-judge / hoj-vue）都有 `restart: unless-stopped`。当 Docker Desktop 重启或系统关机后，MySQL 不会自动恢复，backend 启动即报 500。

**修复**（已应用到 `docker-compose.yml`）：
```yaml
# hoj-mysql：新增 restart 策略
restart: unless-stopped

# hoj-backend：改为健康依赖（原来只检查启动，不检查 MySQL 是否就绪）
depends_on:
  hoj-mysql: { condition: service_healthy }
```

**手动恢复**（如已发生）：
```bash
docker compose up -d hoj-mysql
# hoj-backend 在 MySQL ready 后自动重连，约 10s 恢复
```

---

## 快速健康检查

```bash
# 检查所有服务状态
echo "=== 基础设施 ==="
echo -n "PostgreSQL: " && docker exec open436-postgres pg_isready -U open436 2>&1
echo -n "Redis: " && docker exec open436-redis redis-cli ping 2>&1
echo -n "Consul: " && curl -s http://localhost:8500/v1/status/leader | head -c 20
echo ""
echo -n "Kong: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
echo ""
echo -n "MinIO: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live
echo ""
echo -n "FileService: " && curl -s http://localhost:8007/health | grep -o '"status":"[^"]*"'

echo ""
echo "=== 业务服务 ==="
echo -n "Auth: " && curl -s http://localhost:8081/actuator/health | grep -o '"status":"[^"]*"' | head -1
echo -n "Enrollment: " && curl -s http://localhost:8084/actuator/health | grep -o '"status":"[^"]*"' | head -1
echo -n "Forum: " && curl -s http://localhost:8003/health/ | grep -o '"status":"[^"]*"'
echo -n "AI: " && curl -s http://localhost:8008/health | grep -o '"status":"[^"]*"'

echo ""
echo "=== 前端 ==="
echo -n "Frontend: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
echo ""
echo -n "Admin: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/
echo ""

echo ""
echo "=== HOJ (可选) ==="
echo -n "hoj-mysql: " && docker exec open436-hoj-mysql mysqladmin ping -h localhost -uroot -p${HOJ_MYSQL_PASS:-hoj123456} 2>&1 | head -1
echo -n "hoj-backend: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:6688/api/get-website-config 2>&1
echo ""
echo -n "hoj-judge: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/ 2>&1
echo ""
echo -n "hoj-vue: " && curl -s -o /dev/null -w "%{http_code}" http://localhost:8066/ 2>&1
echo ""
```
