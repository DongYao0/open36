# Open436 生产部署说明

本目录包含 Open436 在 Ubuntu Linux 上**全容器化**生产部署的全部产物。

## 架构概览

```
                       Cloudflare Quick Tunnel (--profile tunnel)
                                     │
                              ┌──────▼──────┐
                              │  public-web │   (聚合 Landing/Frontend/API/Algo/Objects/Honors)
                              │   :80       │
                              └──┬───────────┘
                                 │ /api/* → Kong
                                 │
        ┌──────────┬─────────────┼─────────────┬──────────┐
        │          │             │             │          │
    ┌───▼──┐   ┌───▼──┐    ┌─────▼─────┐  ┌────▼────┐  ┌──▼────┐
    │ Auth │   │Enrol.│    │ FileSvc   │  │ Forum   │  │  AI   │
    │ :8081│   │ :8084│    │ :8007     │  │ :8003   │  │ :8008 │
    └───┬──┘   └──┬───┘    └─────┬─────┘  └────┬────┘  └──┬────┘
        └─────────┴──────┬───────┴────────────┴─────────┘
                         │
   Postgres │ Redis │ Milvus/etcd │ Consul │ MinIO │ Kong │ HOJ*
                  （全部仅 Docker 内部网络）

        Admin (LAN 绑定，仅 ${ADMIN_BIND_IP}:3001，不进 Cloudflare)
```

## 前置条件

- Ubuntu Linux（x86_64）
- Docker Engine ≥ 24.0
- docker compose plugin（`docker compose` v2）
- 实验室网卡已挂载目标 IP（如 `172.20.193.162`），否则 Admin 容器启动报错
- 若启用 `--profile hoj`：联网构建会拉取固定的 `criyle/go-judge:v1.12.0`
  基础镜像；无法访问 Docker Hub 时按 `deploy/prod/go-judge/README.md` 离线导入

## 首次部署

```bash
# 1) 复制并填写环境变量（生产 .env 不入库）
cp deploy/prod/.env.production.example deploy/prod/.env.production
$EDITOR deploy/prod/.env.production

# 强密钥生成示例（每个密钥独立生成，不要复用）：
#   openssl rand -hex 32        # POSTGRES_PASSWORD / REDIS_PASSWORD（URL 安全字符）
#   openssl rand -base64 48     # DJANGO_SECRET_KEY（≥50 字符）/ HOJ_JWT_SECRET / JUDGE_TOKEN
#   htpasswd -bnBC 10 "" 'YourStrongPass' | tr -d ':\n'   # ADMIN_BOOTSTRAP_PASSWORD_HASH
#   （BCrypt 哈希必须用单引号写入 .env，防止 Compose 把 $ 解析成变量）

# 2) 前置检查（.env 存在性、占位符、Admin IP 是否在本机网卡）
bash deploy/prod/scripts/precheck.sh

# 3) 验证 Compose 配置可解析
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml config
```

> **安全设计说明**：不带 `--env-file` 直接执行
> `docker compose -f deploy/prod/compose.yml config` 会因为生产密钥
> （`POSTGRES_PASSWORD`、`JUDGE_TOKEN`、`ADMIN_BOOTSTRAP_*` 等）没有默认值而**报错失败**。
> 这是刻意为之的防呆设计——生产密钥只允许来自 `deploy/prod/.env.production`，
> 仓库与 Compose 文件内不提供任何弱默认密码让裸命令"凑合通过"。
> 因此**所有正式命令都必须携带** `--env-file deploy/prod/.env.production`。

```bash

# 4) 首次完整构建并启动（Open436 + HOJ + Quick Tunnel）
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml --profile hoj --profile tunnel up -d --build

# 5) 如需 AI 联网搜索，再启用 CrawlerService + SearXNG
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml --profile crawler up -d --build
```

HOJ 的空 MySQL 数据卷会自动导入仓库内 `hoj.sql`，随后删除历史弱口令 root
账号和未安装运行时对应的本地语言。首次 Open436 管理员进入“算法管理”时，
同步接口会在 HOJ 中创建同名超级管理员；初始化 SQL 只在空数据卷执行。

## Kong 初始化说明

生产 Kong 使用 **DB-less 声明式模式**，**无需**传统的
`kong migrations bootstrap` / `kong migrations up` 步骤，也不依赖独立的
Kong 数据库：

- 路由表来自 `deploy/prod/kong/kong.yml`（`KONG_DECLARATIVE_CONFIG`），
  以只读方式挂载进容器；
- 自定义 `satoken-auth` 插件（Lua 源码在 `deploy/prod/kong/satoken-auth/`）
  已烘焙进 `deploy/prod/kong/Dockerfile` 构建的专用镜像 `open436/kong:3.4`，
  通过 `KONG_PLUGINS=bundled,satoken-auth` 启用；
- 修改 `kong.yml` 后无需重建镜像，重新创建 kong 容器即可生效：
  `docker compose --env-file deploy/prod/.env.production -f deploy/prod/compose.yml up -d kong`；
- 修改插件 Lua 源码或 Dockerfile 后需要 `build kong` 再 `up -d kong`。

## 查看日志

```bash
# 跟踪某个服务的日志（示例：auth / forum / public-web）
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml logs -f --tail=100 auth

# HOJ / Crawler 属于可选 profile，查看日志同样需要带 profile
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml --profile hoj logs -f --tail=100 hoj-backend hoj-judge

# 单容器最近日志
docker logs --tail=200 open436-prod-public-web
```

## 查看随机网址（Cloudflare Quick Tunnel）

```bash
docker logs open436-prod-cloudflared 2>&1 \
  | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1
```

public-web 会把同源 API 请求的 `Origin` 清除后再转发到内部服务，因此随机网址
每次变化时不需要修改 `CORS_ALLOWED_ORIGINS` 或重启后端。

## 健康检查

```bash
# 容器状态
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml --profile hoj --profile crawler --profile tunnel ps

# 服务内部健康
docker exec open436-prod-kong kong health
docker exec open436-prod-postgres pg_isready -U open436
docker exec open436-prod-redis sh -c 'redis-cli -a "$REDIS_PASSWORD" ping'

# public-web 未发布宿主机端口：先做容器内检查
docker exec open436-prod-public-web curl -fsS http://localhost/
docker exec open436-prod-public-web curl -fsS http://localhost/app/
# 再使用上节日志中得到的 Quick Tunnel 地址做公网端到端检查
curl -fsS https://<random>.trycloudflare.com/
curl -fsS https://<random>.trycloudflare.com/app/
#   Admin（仅 LAN）
curl -fsS http://${ADMIN_BIND_IP}:${ADMIN_BIND_PORT}/
```

## 增量发布（仅重建受影响服务）

```bash
# 例如：只改 Frontend
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml build public-web
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml up -d public-web

# 例如：改了 Auth
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml build auth kong
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml up -d auth kong
```

Kong 插件或 Dockerfile 变更时重建 `kong`；仅 `kong.yml` 变更时重新创建
`kong` 容器即可，无需重建镜像。

## 停止与数据保护

```bash
# 优雅停止（保留所有数据卷）
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml down

# 严禁 docker compose down -v / docker volume rm
# 生产 .env 与所有命名卷均需保留，丢失会导致密钥与数据库不可逆损失。
```

## 数据备份

```bash
bash deploy/prod/scripts/backup.sh
# 产物在 deploy/prod/backups/<timestamp>/ 下：
#   ${POSTGRES_DB}.sql.gz   ← 由 .env.production 中 POSTGRES_DB 决定（旧默认 open436）
#   ai_db.sql.gz
#   hoj.sql.gz             ← 仅在 --profile hoj 启用且容器运行时生成
#   minio/<MINIO_BUCKET>/  ← 对象镜像
```

### 退出码（运维必读）

| 退出码 | 含义 | 触发条件 |
|---|---|---|
| `0`  | 全部成功 | 所有已运行的目标服务均成功备份 |
| `2`  | 部分失败 | 至少一个目标 pg_dump / mysqldump / mc mirror 失败 |
| `3`  | 无目标可备份 | 全部服务均未运行（`OK=0`、`FAIL=0`）——脚本不会伪装成功 |

### 完整性校验（**仅 gzip 解压测试**，不是恢复演练）

```bash
BACKUP_INTEGRITY_CHECK=1 bash deploy/prod/scripts/backup.sh
# 依次 gunzip -t <each .sql.gz>，仅验证文件可解压，不验证内容正确性。
```

### 恢复流程（**必须先停止应用**才能恢复数据库）

```bash
# 1) 停止应用层服务（但保留 Postgres/MySQL/MinIO 容器运行）
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml stop forum-service file-service ai-service auth enrollment \
                                                 public-web admin hoj-backend hoj-judge hoj-vue

# 2) 执行恢复（脚本会二次确认，除非 RESTORE_FORCE=1）
bash deploy/prod/scripts/restore.sh deploy/prod/backups/<timestamp>/

# 3) 使用与部署时相同的 profile 重新启动所有服务
docker compose --env-file deploy/prod/.env.production \
  -f deploy/prod/compose.yml --profile hoj --profile tunnel up -d

# 严禁 docker compose down -v（会删除命名卷，丢失数据库与 .env）；
# 严禁 docker volume rm（同样会丢失数据）。
```

`restore.sh` 自动识别备份文件中业务库的命名：
- 优先匹配 `${POSTGRES_DB}.sql.gz`（与 `backup.sh` 新格式一致）
- 兼容旧 `open436.sql.gz`（历史备份）
- 同时处理 `ai_db.sql.gz` / `hoj.sql.gz` / MinIO `mc mirror` 反向同步

**隔离恢复演练注意**（不对生产容器执行时）：
- 备份由 `pg_dump`/`mysqldump` 原样导出，含 `ALTER ... OWNER TO ${POSTGRES_USER}`。
  演练用临时 PostgreSQL 必须先创建与生产一致的 `${POSTGRES_USER}` 角色和
  `${POSTGRES_DB}` / `ai_db` 两个数据库，否则导入会在 OWNER 语句处中断
  （生产容器初始化时天然满足这些条件）。
- 演练用临时 MySQL 必须以生产同款参数启动，至少包含
  `--restrict-fk-on-non-standard-key=OFF`，否则 HOJ 遗留 schema 的外键
  （指向非唯一索引）会在导入时报 `Missing unique key` 中断。
- 演练容器用 `docker run --rm` 启动、结束 `docker stop` 即自动清理；
  严禁对生产卷执行任何恢复演练。

## 开发环境隔离

| 维度 | 开发 | 生产 |
|---|---|---|
| Compose 项目名 | `open436` / `open436-dev` | `open436-prod` |
| 网络子网 | `172.28.0.0/16` | `172.29.0.0/16` |
| 卷前缀 | `open436-*` / `open436-dev-*` | `open436-prod-*` |
| .env 文件 | `.env`（开发默认值） | `deploy/prod/.env.production` |
| 前端热更新 | `volumes: [.]:/app` | 镜像烘焙（无 bind mount） |
| 入口端口 | 多端口调试暴露 | 仅 Admin LAN + cloudflared 入口 |

## 故障排查

### Auth/Enrollment Flyway 启动冲突

两者共用同一 `open436` 数据库。生产 profile 下：

- Auth：`spring.flyway.table=auth_flyway_schema_history`
- Enrollment：`spring.flyway.table=enrollment_flyway_schema_history`

两个服务使用独立 history 表，可安全先后启动。遇到迁移失败时先备份并查看对应
服务日志；不要删除 history 表，也不要盲目执行 Flyway repair。

### FileService 无法在干净 Linux 构建

需要 `.sqlx/` 与 `Cargo.lock` 两个文件均提交仓库（已配置）。如需重新生成：
`bash deploy/prod/scripts/gen-sqlx-offline.sh`。

### HOJ 判题机连不上 go-judge 沙箱

历史补丁依赖（`localhost:5050` 字节码 patch）已**废除**。当前由源码
`SandboxRun.java:69` 的 `System.getenv("SANDBOX_URL")` 直接读取，生产 compose
中以环境变量 `SANDBOX_URL=http://go-judge:5050` 注入。

### Admin 启动报 "address not available"

`ADMIN_BIND_IP` 在本机网卡上不存在。运行 `ip addr` 或 Windows `ipconfig` 确认；
改 `.env.production` 中的 `ADMIN_BIND_IP` 为真实存在的实验室网卡 IP；生产环境
不要改成 `0.0.0.0`，否则管理端会监听全部网卡。

### 算法管理入口

生产 Admin 的“算法管理”直接进入同源 `/algo/admin/dashboard`，由 Open436 Auth
完成 HOJ 单点同步。旧 `/quiz` 页面仍是开发原型，但生产导航和仪表盘均不再暴露
该入口，算法题 CRUD 统一由 HOJ 管理端承担。

### HOJ 语言运行时覆盖

详见 [`deploy/prod/go-judge/README.md`](go-judge/README.md)。生产镜像只保证
C / C++ / Python3 / PHP / Ruby / Node.js / Java / Go 可用；**Python2、PyPy2、
PyPy3、Rust、C# 当前已从 `language.yml` 中移除**，避免提交后在生产选了该
语言却执行失败。
