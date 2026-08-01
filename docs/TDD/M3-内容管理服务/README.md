# M3/M4/M5 - Forum 论坛服务技术设计文档

## 文档概述

本文件夹包含 **Forum 论坛服务 (Open436-Forum)** 的技术设计文档。

> ⚠️ **架构说明**：Forum 是一个 Django 单体服务，承载了三个业务模块：
> - **M3 内容管理** — 帖子 CRUD、状态管理
> - **M4 评论与互动** — 回复、点赞、收藏
> - **M5 板块管理** — 板块 CRUD、排序
>
> 三个模块共享同一数据库和进程，通过 Django App 划分职责。

**技术栈**: Python 3.11+ + Django 4.2+ + Django REST Framework + PostgreSQL

**服务端口**: 8003

---

## 服务架构

```
Forum Service :8003 (Django)
├── apps/content/      # M3 内容管理
│   ├── models.py      # Post, PostVersion
│   ├── views.py       # 公开 API
│   └── views_internal.py  # 内部 API
├── apps/comment/      # M4 评论与互动
│   ├── models.py      # Reply, Like, Favorite
│   ├── views.py       # 公开 API
│   └── views_internal.py  # 内部 API
├── apps/section/      # M5 板块管理
│   ├── models.py      # Section
│   ├── views.py       # 公开 API
│   └── views_internal.py  # 内部 API
└── apps/core/         # 公共组件
    ├── middleware.py   # Sa-Token 鉴权中间件
    ├── permissions.py  # 权限检查
    ├── consul_client.py  # Consul 注册
    └── file_service_client.py  # 文件服务调用
```

---

## Django App 划分

### content（M3 内容管理）

| 模型 | 说明 |
|------|------|
| Post | 帖子（标题、内容、作者、板块、状态） |
| PostVersion | 帖子版本历史 |

**API 路径**: `/api/posts/`

### comment（M4 评论与互动）

| 模型 | 说明 |
|------|------|
| Reply | 回复 |
| Like | 点赞 |
| Favorite | 收藏 |

**API 路径**: `/api/comments/`, `/api/replies/`

### section（M5 板块管理）

| 模型 | 说明 |
|------|------|
| Section | 板块（名称、slug、颜色、排序、启用状态） |

**API 路径**: `/api/sections/`

---

## 服务间通信

### 依赖的服务

| 服务 | 通信方式 | 说明 |
|------|---------|------|
| Open436-Auth | HTTP (Consul) | 用户鉴权、获取用户信息 |
| Open436-FileService | HTTP (Consul) | 图片上传 |
| Consul | HTTP | 服务注册与发现 |

### 内部 API（供其他服务调用）

| 路径 | 说明 |
|------|------|
| `/internal/posts/` | 帖子内部接口 |
| `/internal/comments/` | 评论内部接口 |
| `/internal/sections/` | 板块内部接口 |

---

## 详细文档

- [M5 板块管理 TDD](../M5-板块管理服务/) — 板块模块的详细设计
- [M3 内容管理 PRD](../../PRD/M3-内容管理模块.md) — 内容模块需求
- [M4 评论与互动 PRD](../../PRD/M4-评论与互动模块.md) — 评论模块需求

---

**创建日期**：2026-06-14
