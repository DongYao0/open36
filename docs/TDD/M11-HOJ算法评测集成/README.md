# M11 - HOJ 算法评测集成

## 概述

HOJ（Hcode Online Judge）是集成到 Open436 平台的在线算法评测系统，基于开源 HOJ 项目二次开发。

**不是自研模块**，而是第三方系统的集成部署。

---

## 服务组成

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| HOJ Backend | open436-hoj-backend | 6688 | Spring Boot + Shiro + JWT |
| HOJ Judge | open436-hoj-judge | 8088 | 判题服务 |
| HOJ Vue | open436-hoj-vue | 8066 | Vue 2 + Element UI 前端 |
| HOJ MySQL | open436-hoj-mysql | 3308 (→3306) | MySQL 8.0 专用数据库 |
| go-judge | go-judge | 5050 | 沙箱判题引擎 |

---

## SSO 单点登录

### 认证体系

HOJ 使用独立的认证体系（Shiro + JWT），与 Open436 的 Sa-Token 完全独立。

### 同步流程

```
Open436-Admin 侧边栏点击"算法管理"
  │
  ▼
POST /api/auth/algo-sync (Auth 服务, Sa-Token 鉴权)
  │
  ├── 验证用户状态为 active
  ├── 获取用户角色
  │
  ▼
POST http://localhost:6688/api/open436-sync (HOJ 后端)
  │  Body: { username, nickname, avatar, apiKey, role }
  │
  ├── HOJ 创建/更新用户
  ├── 返回 JWT Token (Authorization header)
  │
  ▼
Auth 服务保存 hoj_user_mapping (authUserId ↔ hojUuid)
  │
  ▼
返回 HOJ JWT Token 给前端
  │
  ▼
前端跳转: http://localhost:8066/algo/admin/dashboard?hoj_token=xxx&username=xxx&role=xxx
  │
  ▼
HOJ Vue beforeEach 读取 URL 参数 → 存入 localStorage → 进入管理后台
```

### 默认管理员

| 系统 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| HOJ | root | root123 | HOJ 内置超级管理员 |
| Open436 | admin | admin123 | Open436 管理员，通过 SSO 同步到 HOJ |

---

## HOJ 后端配置

**关键配置**（`application-dev.yml`）：

```yaml
server:
  port: 6688

# HOJ 专用 MySQL
mysql-host: 127.0.0.1
mysql-port: 3307        # Docker 映射为 3308
mysql-username: root
mysql-password: hoj123456
mysql-name: hoj

# Redis (共享 Open436 的 Redis)
redis-host: 127.0.0.1
redis-port: 6379

# Open436 SSO 集成
hoj:
  sync:
    api-key: open436-secret-key
```

---

## Docker Compose 启动

```bash
# 启动 HOJ 相关服务
docker compose --profile hoj up -d

# 包含的服务:
# - go-judge (沙箱)
# - hoj-mysql (数据库)
# - hoj-backend (后端)
# - hoj-judge (判题)
# - hoj-vue (前端)
```

---

## 注意事项

1. **HOJ 使用 Shiro + JWT**，不是 Sa-Token。两个认证体系完全独立。
2. **HOJ 有独立的 MySQL 数据库**，不与 Open436 的 PostgreSQL 共享。
3. **HOJ Redis 与 Open436 Redis 共享**（同一容器，端口 6380→6379）。
4. **管理端必须通过 SSO 进入**，直接访问 HOJ 管理端会显示"未登录"。
5. **HOJ Vue 前端是 Vue 2**，与 Open436 的 Vue 3 技术栈不同。

---

**创建日期**：2026-06-14
