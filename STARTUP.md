# Open436 启动指南

> **本项目唯一权威启动文档**。整合真实可用启动命令、实测问题与解决方案（2026-08-01 全栈实测定稿）。
> `docs/guides/启动流程报告.md`（2026-06-10 旧版）已废弃，统一以本文为准。

## 一、架构概览

Open436 教育平台采用**混合部署**：
- **Docker**：基础设施（PostgreSQL/Redis/Consul/Kong/MinIO/Milvus）+ HOJ 判题系统 + FileService(Rust)
- **本地**：Java 业务服务（Auth/Enrollment）+ Python 服务（Forum/AI）+ 前端（Vue/Admin/Landing）

## 二、服务清单

| 分类 | 服务 | 端口 | 运行方式 | 说明 |
|---|---|---|---|---|
| 基础设施 | postgres | 55400 | Docker | 主数据库 |
|  | redis | 6380 | Docker | 缓存 + Sa-Token Session |
|  | consul | 8500 | Docker | 服务注册发现 |
|  | kong / kong-db | 8000/8001 | Docker | API 网关 + satoken-auth 插件 |
|  | minio | 9000/9001 | Docker | 对象存储 |
|  | etcd | — | Docker | Milvus 元数据（仅 Docker 内网，未映射宿主） |
|  | milvus | 19530 | Docker | 向量库（AI 依赖） |
|  | file-service | 8007 | Docker | 文件服务 (Rust Actix) |
| HOJ | hoj-mysql | 3308 | Docker | HOJ 专用 MySQL |
|  | go-judge | 5050 | Docker | 判题沙箱 |
|  | hoj-backend | 6688 | Docker | HOJ 后端 API |
|  | hoj-judge | 8088 | Docker | 判题服务 |
|  | hoj-vue | 8066 | Docker | HOJ 前端 |
| 业务 | auth-service | 8081 | 本地 mvn | 认证 (Spring Boot 3.5) |
|  | enrollment-service | 8084 | 本地 mvn | 报名 (Spring Boot 3.5) |
|  | forum-service | 8003 | 本地 python | 论坛 (Django，合并 content/comment/section) |
|  | ai-service | 8008 | 本地 python | AI (FastAPI + Multi-Agent) |
| 前端 | Vue 用户前端 | 3000 | 本地 npm | Open436-Frontend |
|  | Admin 管理后台 | 3001 | 本地 npm | Open436-Admin |
|  | Landing 聚合入口 | 5173 | 本地 npm | Open436-Landing（3D 首页 + 反代） |

## 三、启动模式

- **模式1（推荐，本地开发）**：基础设施在 Docker，应用本地运行。**下文详细步骤即此模式**。
- **模式2（全容器化）**：`docker compose -f docker-compose.full.yml up -d --build`（含 HOJ 加 `--profile hoj`），路由配置 `bash docker/init-kong.sh`。

## 四、详细启动步骤（模式1）

> 所有本地长驻服务（Java/Python/前端）都是阻塞式 dev server，须**各自独立终端**或后台运行。

### 步骤 0 · Python 依赖（首次或依赖变更时）

项目使用**统一的项目根 `.venv`**（Forum 与 AIService 共用，无独立 venv）：

```bash
python -m venv .venv                       # 仅首次创建
.venv/Scripts/python.exe -m pip install \
  -r Open436-AIService/requirements.txt \
  -r Open436-Forum/requirements.txt \
  python-multipart langchain-openai
```

> ⚠ `python-multipart`（AI 表单/文件上传）与 `langchain-openai`（AI LLM）**不在 requirements.txt**，必须单独补装，否则 AI 服务报 `ModuleNotFoundError: langchain_openai` 或 `Form data requires "python-multipart"`。

### 步骤 1 · 启动基础设施 + FileService

```bash
docker compose up -d
```

预期：postgres(healthy) / redis / consul / kong(healthy) / minio / etcd / milvus / file-service 全 `Up`。

> ⚠ file-service 首次启动可能因 Docker 网络 DNS 同步延迟 panic（`failed to lookup address information`），见故障排除 #1。

### 步骤 2 · 启动 HOJ 判题系统（可选）

```bash
docker compose --profile hoj up -d
curl http://localhost:6688/api/get-website-config   # 期望 200
```

默认账号：`root / hoj123456`。HOJ MySQL 已配置 `restart: unless-stopped`，Docker 重启后自动恢复。

### 步骤 3 · 启动 Java 业务服务（Auth 8081 / Enrollment 8084）

```bash
mvn -f Open436-Auth/pom.xml spring-boot:run -Dspring-boot.run.profiles=dev
mvn -f Open436-Enrollment/pom.xml spring-boot:run -Dspring-boot.run.profiles=dev
```

验证：`curl http://localhost:8081/actuator/health` → `{"status":"UP"}`。

> 配置文件 `application-dev.yml`：Redis 端口 **6380**、PostgreSQL 端口 **55400**、Consul 8500。Auth 启动约 8s 并自动注册到 Consul。

### 步骤 4 · 启动 Forum 服务（Django，8003）

```bash
cd Open436-Forum
../.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8003
```

验证：`curl http://localhost:8003/health/` → `{"status":"healthy","database":"ok",...}`。

> Forum schema 由 `db-init/` SQL 管理，**非 Django 迁移**（`showmigrations` 永远空属正常）。新增字段须同步 `db-init/V{N}__*.sql`，**勿用 `manage.py migrate`**（会因表已存在失败）。

### 步骤 5 · 启动 AI Service（FastAPI，8008）

```bash
cd Open436-AIService
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

验证：`curl http://localhost:8008/health` → `{"code":200,"data":{"status":"healthy",...}}`。

> ⚠ **必须用 `--host 127.0.0.1`**。Windows 上 `0.0.0.0:8008` 会报 `WinError 10048`（端口保留/旧进程残留），见故障排除 #7。

### 步骤 6 · 启动前端（Vue 3000 / Admin 3001 / Landing 5173）

**启动顺序很重要**——Landing 是聚合入口（反代 Vue），须最后启：

```bash
# 1) Vue 用户前端（:3000，不自动开浏览器）
cd Open436-Frontend && npm run dev

# 2) Admin 管理后台（:3001）
cd Open436-Admin && npm run dev

# 3) Landing 聚合入口（:5173，open:true 自动开浏览器）
cd Open436-Landing && npm run dev
```

> ⚠ Vue `vite.config.js` 须 `open:false`、Landing 须 `open:true`。否则浏览器会误开 `:3000/` 跳转到不存在的 Landing 根导致空白页。直接访问业务用 `http://localhost:3000/app/`。

### 步骤 7 · 配置 Kong 路由

```bash
bash deploy/dev/kong-config.sh
```

脚本用 `host.docker.internal` 作上游地址，先 DELETE 再 CREATE（幂等）。注册 4 条路由：
- auth-service → `/api/auth/*`、`/api/users/*`
- file-service → `/api/files/*`（+ satoken-auth 插件）
- enrollment-service → `/api/enrollment/*`
- forum-service → `/api/posts/*`、`/api/comments/*`、`/api/sections/*`、`/api/replies/*` 等

> ⚠ 若脚本报 `409 Conflict` / `foreign key violation`，说明旧路由残留（见故障排除 #5），须先清理再重跑。

## 五、访问地址

| 用途 | 地址 |
|---|---|
| **Landing 聚合入口（推荐）** | http://localhost:5173/ |
| Vue 用户前端 | http://localhost:3000/app/ |
| Admin 管理后台 | http://localhost:3001/ |
| Kong 代理 | http://localhost:8000 |
| Kong 管理 API | http://localhost:8001 |
| HOJ 算法前端 | http://localhost:8066/ |
| Consul UI | http://localhost:8500 |
| MinIO Console | http://localhost:9001 |

## 六、服务间依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                  Landing :5173 (聚合入口, React)                 │
│   /  → 3D首页   /app/* → Vue:3000   /api/* → 后端   /algo → HOJ  │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Kong API Gateway (:8000)                       │
│                   (satoken-auth 插件鉴权)                        │
└───────┬──────────┬──────────┬──────────┬──────────┬────────────┘
        ▼          ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │  Auth  │ │Enrollmt│ │ Forum  │ │  File  │ │   AI   │
   │ :8081  │ │ :8084  │ │ :8003  │ │ :8007  │ │ :8008  │
   └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
       └──────────┴────┬─────┴────────┴────────┴────────┘
                       ▼
              ┌──────────────┐  ┌──────────┐  ┌──────────┐
              │ PostgreSQL   │  │  Redis   │  │ Milvus   │
              │   :55400     │  │  :6380   │  │ :19530   │
              └──────────────┘  └──────────┘  └──────────┘
```

**依赖**：Auth→PG+Redis · Enrollment→PG+Redis+Auth · Forum→PG · FileService→PG+MinIO · AI→PG+Redis+Milvus+Forum+Auth

## 七、网络架构

```
浏览器
  ↓
localhost:5173 (Landing - 本地 npm, 聚合入口)
  ├── /           → React 3D 首页
  ├── /app/*      → 反代 Vue:3000 (本地)
  ├── /api/*      → 反代 Vue:3000 → Kong:8000 → 各业务服务
  └── /algo       → 反代 Vue:3000 → hoj-vue:8066 (Docker)

localhost:3000 (Vue Frontend - 本地 npm)
  └── /api/*      → Kong:8000 → 业务服务 (本地/Docker)

localhost:3001 (Admin - 本地 npm)
  ├── /api/ai/                              → ai-service:8008 (本地)
  ├── /api/enrollment|assignment|interview  → enrollment:8084
  ├── /api/posts|sections                   → forum:8003
  └── /api/admin/role|user                  → hoj-backend:6688 (Docker)

Docker 网络 (open436-net):
  基础设施: postgres/redis/consul/kong/minio/etcd/milvus/file-service
  HOJ(可选): hoj-mysql/go-judge/hoj-backend/hoj-judge/hoj-vue
```

## 八、故障排除（实测）

### 1. file-service DNS 解析失败（panic）★实测
**现象**：`Restarting(101)`，日志 `failed to lookup address information: Name or service not known`
**原因**：Docker 网络 DNS 同步延迟，启动时无法解析 `postgres` 主机名（即便 postgres 已 healthy）
**解决**：`docker compose up -d --force-recreate file-service`

### 2. Kong 未运行
**现象**：`docker compose ps` 看不到 kong
**解决**：`docker compose up -d kong`；顽固时 `docker compose up -d --force-recreate kong-db kong-migration kong`

### 3. Python 依赖缺失 ★实测
**现象**：`ModuleNotFoundError: langchain_openai` 或 `Form data requires "python-multipart"`
**解决**：`.venv/Scripts/python.exe -m pip install langchain-openai python-multipart`

### 4. Auth Schema 验证失败
**现象**：`Schema-validation: wrong column type`
**解决**：`application-dev.yml` 设 `spring.jpa.hibernate.ddl-auto: update`

### 5. Kong 路由配置冲突（409 / foreign key violation）★实测最棘手
**现象**：`kong-config.sh` 报 `409 Conflict`、`foreign key violation`，路由重复累积，残留废弃的 content/comment/section/user-service
**原因**：旧 routes 引用 services 致 DELETE 失败 → 新建同名 service 冲突 → routes 被反复追加
**解决**：先全量清理再重跑：
```bash
# 清理所有 routes
for id in $(curl -s http://localhost:8001/routes | grep -oE '"id":"[^"]*"' | sed 's/"id":"//;s/"//'); do
  curl -s -X DELETE "http://localhost:8001/routes/$id"; done
# 清理所有 services
for n in $(curl -s http://localhost:8001/services | grep -oE '"name":"[^"]*"' | sed 's/"name":"//;s/"//'); do
  curl -s -X DELETE "http://localhost:8001/services/$n"; done
# 清理 plugins（同 routes，用 id），然后重跑
bash deploy/dev/kong-config.sh
```

### 6. 首页跳转到 :3000 而非 :5173 ★实测
**现象**：浏览器开 `:3000/` 跳空白页（非 3D 首页）
**原因**：Vue `open:true` 误开浏览器；`:5173`（Landing）才是聚合入口，Vue 在 `/` 会跳回 Landing 根
**解决**：Vue `vite.config.js` 设 `open:false`、Landing 设 `open:true`。直接访问 `:3000/app/` 或 `:5173/`

### 7. AI 端口绑定失败 WinError 10048 ★实测
**现象**：`[winerror 10048] bind on address ('0.0.0.0', 8008)`
**解决**：改用 `--host 127.0.0.1`（见步骤 5），开发仅需本地访问

### 8. Kong 路由 host 指向旧 IP 导致 502
**现象**：`curl :8000/api/auth/register` 返回 502，直连 :8081 正常
**原因**：旧路由 host 为失效的开发机 IP
**解决**：`curl -X PATCH http://localhost:8001/services/auth-service --data host=host.docker.internal --data port=8081`

### 9. HOJ MySQL 不自动重启
**现象**：hoj-backend 报 `CommunicationsLinkFailure: UnknownHostException: hoj-mysql`
**解决**：`docker-compose.yml` 已为 hoj-mysql 加 `restart: unless-stopped`、hoj-backend 改 `service_healthy` 依赖。手动恢复：`docker compose up -d hoj-mysql`

### 10. git 拉取误删文件恢复 ★实测重大事件
**现象**：拉取后 `Open436-Landing` / `Open436-hoj` / `prototype` / `src` 大量文件消失（`4ca6e09` 误删 534 文件，提交信息仅 "open36" 未提示）
**解决**：从拉取前提交恢复（保留后续提交的合理改动）：
```bash
# 全量恢复所有"误删且未重建"的文件
git diff 1ba53d9 --diff-filter=D --name-only -z | xargs -0 git checkout 1ba53d9 --
git commit -m "恢复 4ca6e09 误删的文件"
```

## 九、快速健康检查

```bash
echo "--- 基础设施 ---"
echo -n "PG: "    && docker exec open436-postgres pg_isready -U open436 2>&1 | head -1
echo -n "Redis: " && docker exec open436-redis redis-cli ping
echo -n "Kong: "  && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/sections/
echo -n "File: "  && curl -s http://localhost:8007/health | grep -o '"status":"[^"]*"'
echo "--- 业务 ---"
echo -n "Auth: "  && curl -s http://localhost:8081/actuator/health | grep -o '"status":"[^"]*"' | head -1
echo -n "Enroll: "&& curl -s http://localhost:8084/actuator/health | grep -o '"status":"[^"]*"' | head -1
echo -n "Forum: " && curl -s http://localhost:8003/health/ | grep -o '"status": *"[^"]*"'
echo -n "AI: "    && curl -s http://localhost:8008/health | grep -o '"status":"[^"]*"'
echo "--- 前端 ---"
for p in 3000 3001 5173; do echo -n ":$p " && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:$p/; done
echo "--- HOJ ---"
echo -n "hoj-backend: " && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:6688/api/get-website-config
```

## 十、常用运维命令

```bash
docker compose ps                       # 容器状态
docker compose logs -f file-service     # 跟踪日志
docker compose restart kong             # 重启单个服务
docker compose down                     # 停止基础设施
docker compose --profile hoj down       # 停止 HOJ
curl http://localhost:8001/services     # Kong 已注册服务
curl http://localhost:8001/routes       # Kong 路由
```

## 十一、文档维护

- 本文档是 Open436 **唯一权威启动文档**。旧版 `docs/guides/启动流程报告.md`（2026-06-10）已废弃重定向至此。
- 启动流程或端口变更须同步更新本文「服务清单」表与对应步骤。
- 最后定稿：2026-08-01（全栈启动实测定稿）。





