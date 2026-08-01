# Open436 - 社团招新与技术论坛平台

## 项目简介

Open436 是一个综合性社团管理平台，包含招新管理、论坛交流、算法训练（HOJ）、AI 助手等功能模块。采用微服务架构，前后端分离。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户浏览器                                  │
├──────────────────────┬──────────────────────────────────────────┤
│  Open436-Frontend    │  Open436-Admin         │  HOJ-Vue        │
│  (论坛前端 :3000)     │  (管理后台 :3001)       │  (算法前端 :8066) │
│  Vue 3 + Vite        │  Vue 3 + Element Plus  │  Vue 2 + Element │
└──────────┬───────────┴───────────┬────────────┴────────┬────────┘
           │                       │                     │
           ▼                       ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Vite Dev Proxy / Nginx                        │
└──────────────────────────────────────────────────────────────────┘
           │                       │                     │
     ┌─────┴─────┐          ┌─────┴─────┐         ┌────┴────┐
     ▼           ▼          ▼           ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌──────┐ ┌──────┐
│Auth :8081│ │Forum:8003│ │Enroll : │ │AI:8008 │ │HOJ   │ │File  │
│Spring Boot│ │Django   │ │8084     │ │FastAPI │ │:6688 │ │:8007 │
│Sa-Token  │ │DRF      │ │Spring   │ │        │ │Shiro │ │FastAPI│
└────┬─────┘ └────┬────┘ └────┬────┘ └───┬────┘ └──┬───┘ └──┬───┘
     │            │           │           │         │        │
     └────────────┴───────────┴───────────┴─────────┴────────┘
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼            ▼           ▼           ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐
│PostgreSQL│ │  Redis   │ │  Consul  │ │ MinIO  │ │  Milvus  │
│ :55400   │ │ :6380    │ │ :8500    │ │:9000   │ │ :19530   │
│(Auth/Enr)│ │(缓存/Session)│ │(服务发现) │ │(对象存储)│ │(向量检索) │
└──────────┘ └─────────┘ └─────────┘ └────────┘ └──────────┘
```

## 服务端口一览

| 服务 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| **Open436-Frontend** | 3000 | Vue 3 + Vite | 论坛前端 |
| **Open436-Admin** | 3001 | Vue 3 + Vite + Element Plus | 管理后台前端 |
| **Open436-Auth** | 8081 | Spring Boot + Sa-Token + JPA | 认证授权服务 |
| **Open436-Enrollment** | 8084 | Spring Boot + Sa-Token + JPA | 招新管理服务 |
| **Forum Service** | 8003 | Django REST Framework | 论坛内容服务 |
| **AI Service** | 8008 | Python (LangChain) | AI 助手服务 |
| **File Service** | 8007 | FastAPI + MinIO | 文件存储服务 (Docker) |
| **HOJ Backend** | 6688 | Spring Boot + Shiro + JWT | 算法评测后端 (Docker) |
| **HOJ Judge** | 8088 | Spring Boot | 判题服务 (Docker) |
| **HOJ Vue** | 8066 | Vue 2 + Element UI | 算法前端 (Docker) |
| **Kong Gateway** | 8000 | Kong 3.4 | API 网关 (Docker) |
| **PostgreSQL** | 55400 | PostgreSQL 14 | 主数据库 (Docker) |
| **Redis** | 6380 | Redis 7 | 缓存/Session (Docker) |
| **Consul** | 8500 | Consul 1.17 | 服务注册发现 (Docker) |
| **MinIO** | 9000/9001 | MinIO | 对象存储 (Docker) |
| **Milvus** | 19530 | Milvus 2.4 | 向量数据库 (Docker) |
| **HOJ MySQL** | 3308 | MySQL 8.0 | HOJ 专用数据库 (Docker) |

## 快速启动

### 前置要求

- Docker Desktop
- JDK 17+
- Maven 3.8+
- Node.js 18+
- Python 3.11+

### 第一步：启动基础设施

```bash
# 启动基础服务（PostgreSQL、Redis、Consul、MinIO、Kong 等）
docker compose up -d

# 如需 HOJ 算法评测系统，加 --profile hoj
docker compose --profile hoj up -d
```

### 第二步：启动后端服务

```bash
# 终端 1：认证服务
cd Open436-Auth
mvn spring-boot:run

# 终端 2：招新服务
cd Open436-Enrollment
mvn spring-boot:run

# 终端 3：论坛服务（使用项目根 .venv，Forum 与 AIService 共用）
source .venv/bin/activate   # Windows: .venv\Scripts\activate（在项目根目录执行）
cd Open436-Forum
python manage.py runserver 0.0.0.0:8003   # 必须 0.0.0.0，否则 Kong 容器经 host.docker.internal 无法访问

# 终端 4：AI 服务（使用项目根 .venv）
cd Open436-AIService
python -m uvicorn app.main:app --host 0.0.0.0 --port 8008
```

### 第三步：启动前端服务

```bash
# 终端 5：论坛前端
cd Open436-Frontend
npm install
npm run dev          # http://localhost:3000

# 终端 6：管理后台
cd Open436-Admin
npm install
npm run dev          # http://localhost:3001
```

### 第四步：访问系统

| 入口 | 地址 | 账号 |
|------|------|------|
| 论坛前端 | http://localhost:3000 | 注册新账号 |
| 管理后台 | http://localhost:3001 | admin / admin123 |
| HOJ 算法平台 | http://localhost:8066 | 从管理后台"算法管理"进入（自动同步） |
| Kong 管理 | http://localhost:8001 | - |
| Consul UI | http://localhost:8500 | - |
| MinIO 控制台 | http://localhost:9001 | minioadmin / minioadmin |

## 认证说明

系统使用两套独立的认证体系：

| 系统 | 认证框架 | Token 传递方式 | 说明 |
|------|---------|---------------|------|
| Open436 (Auth/Enrollment) | Sa-Token | HTTP Header `token` | 主认证系统 |
| HOJ | Shiro + JWT | HTTP Header `Authorization` | 算法平台独立认证 |

**SSO 单点登录**：管理后台登录后，点击侧边栏"算法管理"会自动调用 `/api/auth/algo-sync` 同步用户到 HOJ 并获取 JWT Token，通过 URL 参数传递给 HOJ 前端。

## 项目结构

```
Open436/
├── Open436-Frontend/        # 论坛前端 (Vue 3)
├── Open436-Admin/           # 管理后台前端 (Vue 3 + Element Plus)
├── Open436-Auth/            # 认证授权服务 (Spring Boot)
├── Open436-Enrollment/      # 招新管理服务 (Spring Boot)
├── Open436-Forum/           # 论坛内容服务 (Django)
├── Open436-AIService/       # AI 助手服务 (Python)
├── Open436-FileService/     # 文件存储服务 (FastAPI)
├── Open436-hoj/             # HOJ 在线评测系统
│   ├── hoj-springboot/      #   后端 (Spring Boot)
│   └── hoj-vue/             #   前端 (Vue 2)
├── deploy/
│   └── dev/                 # 开发环境配置
├── docs/                    # 文档
│   ├── PRD/                 #   产品需求文档
│   └── TDD/                 #   技术设计文档
├── docker-compose.yml       # 基础设施 Docker Compose
└── README.md
```

## 常见问题

### 管理后台显示"请求失败"

浏览器 localStorage 中的 token 可能已过期。清除后重新登录：

```javascript
// 在浏览器 F12 Console 中执行
localStorage.clear();
location.href = '/login';
```

### HOJ 管理端显示"未登录"

必须从管理后台侧边栏点击"算法管理"进入，不能直接访问 HOJ 管理端。HOJ 使用独立的认证体系，需要通过 SSO 同步获取 token。

### 数据库连接失败

确认 PostgreSQL 容器已启动且端口映射正确：

```bash
docker ps | grep postgres
# 应看到 0.0.0.0:55400->5432/tcp
```

## 开发文档

- [产品需求文档](docs/PRD/)
- [技术设计文档](docs/TDD/)
- [部署运维指南](docs/TDD/00-全局架构/05-部署运维指南.md)
