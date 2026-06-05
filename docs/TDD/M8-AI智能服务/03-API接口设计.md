# M8 - AI智能服务 API接口设计

## 文档信息

**文档版本**: v1.1
**创建日期**: 2026-06-01
**最后更新**: 2026-06-05
**文档类型**: 技术设计文档（TDD）

---

## 目录

1. [API概述](#1-api概述)
2. [同步对话接口](#2-同步对话接口)
3. [异步任务接口](#3-异步任务接口)
4. [会话管理接口](#4-会话管理接口)
5. [Agent管理接口](#5-agent管理接口)
6. [错误码定义](#6-错误码定义)

### 1.4 统一响应格式

与现有Python服务（M2-M5）保持一致的响应格式（`Open436-ContentService/apps/core/responses.py`）：

**成功响应**：
```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": { ... }
}
```

**错误响应**：
```json
{
  "code": 40001,
  "message": "消息内容不能为空",
  "timestamp": 1717200000000,
  "errors": { ... }
}
```

---

## 1. API概述

### 1.1 基础信息

| 项目 | 说明 |
|------|------|
| **基础路径** | `/api/ai` |
| **认证方式** | Kong `satoken-auth` 插件自动鉴权（前端携带 `Authorization: Bearer {token}`，Kong验证后注入用户信息Header） |
| **权限要求** | 仅管理员（Kong注入的 `X-User-Role` 必须为 `admin`） |
| **响应格式** | 统一 `{code, message, timestamp, data}` 格式（与现有Python服务一致） |
| **内容类型** | `application/json` |

### 1.3 Kong鉴权机制

M8服务通过Kong网关统一鉴权，**不需要自行验证Token**。Kong的 `satoken-auth` 插件会：

1. 从请求的 `Authorization` Header 提取Token
2. 调用 Auth 服务 `POST /api/auth/verify` 验证Token有效性
3. 验证成功后注入以下Header到M8服务：

| Header | 来源 | 说明 |
|--------|------|------|
| `X-User-Id` | Auth服务返回 | 当前用户ID（BIGINT） |
| `X-Username` | Auth服务返回 | 当前用户名 |
| `X-User-Role` | Auth服务返回 | 角色代码（`admin` / `user`） |
| `X-User-Status` | Auth服务返回 | 账号状态（`active` / `pending` / `disabled`） |

**M8服务的鉴权逻辑**：只需读取Kong注入的Header，检查 `X-User-Role == admin` 即可，无需调用Auth服务。

```python
# FastAPI 依赖注入：验证管理员身份
async def get_current_admin(
    x_user_id: str = Header(alias="X-User-Id"),
    x_user_role: str = Header(alias="X-User-Role"),
) -> int:
    """从Kong注入的Header中获取当前管理员信息"""
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="权限不足：仅管理员可访问")
    return int(x_user_id)
```

> 对比现有Django服务的 `UserInfoMiddleware`（`Open436-ContentService/apps/core/middleware.py`），M8使用FastAPI的依赖注入实现相同功能。

### 1.2 接口总览

| 方法 | 路径 | 说明 | 模式 |
|------|------|------|------|
| `POST` | `/api/ai/chat` | 同步对话 | 同步 |
| `POST` | `/api/ai/tasks` | 创建异步任务 | 异步 |
| `GET` | `/api/ai/tasks` | 查询任务列表 | - |
| `GET` | `/api/ai/tasks/{task_id}` | 查询任务状态 | - |
| `DELETE` | `/api/ai/tasks/{task_id}` | 取消任务 | - |
| `GET` | `/api/ai/conversations` | 查询会话列表 | - |
| `GET` | `/api/ai/conversations/{id}` | 查询会话详情（含消息） | - |
| `DELETE` | `/api/ai/conversations/{id}` | 删除会话 | - |
| `GET` | `/api/ai/agents` | 查询Agent列表 | 管理 |
| `PUT` | `/api/ai/agents/{name}` | 更新Agent配置 | 管理 |

---

## 2. 同步对话接口

### 2.1 POST /api/ai/chat

同步对话，发送消息并等待Agent执行完成返回结果。

**请求头**（由Kong自动注入，M8服务读取即可）：

| Header | 值 | 说明 |
|--------|---|------|
| `Authorization` | `Bearer {token}` | 前端携带，Kong提取并验证 |
| `X-User-Id` | `{user_id}` | Kong注入，当前管理员ID |
| `X-User-Role` | `admin` | Kong注入，必须为admin |

**请求体**：

```json
{
  "message": "在技术分享板块发一篇关于Git基础命令的教程",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | 是 | 管理员输入的消息，1-5000字符 |
| `conversation_id` | string(UUID) | 否 | 会话ID，不传则创建新会话 |

**响应（成功）**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440001",
    "reply": "已在「技术分享」板块发布了帖子《Git基础命令教程》，帖子ID: 123。",
    "intent": "forum",
    "agent_name": "forum",
    "tool_calls": [
      {
        "tool_name": "list_sections",
        "status": "success",
        "duration_ms": 120
      },
      {
        "tool_name": "create_post",
        "status": "success",
        "duration_ms": 350,
        "result_summary": "post_id: 123"
      }
    ],
    "token_usage": {
      "input": 1500,
      "output": 800
    }
  }
}
```

**响应（意图不明确）**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440002",
    "reply": "抱歉，我没有完全理解您的指令。您是想要：\n1. 在论坛发布一篇帖子\n2. 生成一道算法题目\n请告诉我您的具体需求。",
    "intent": "unclear",
    "agent_name": "router",
    "tool_calls": [],
    "token_usage": {
      "input": 200,
      "output": 150
    }
  }
}
```

**错误响应**：

| HTTP状态码 | code | 说明 |
|-----------|------|------|
| 401 | 401 | 未认证 |
| 403 | 403 | 非管理员 |
| 422 | 422 | 参数校验失败 |
| 500 | 500 | Agent执行异常 |
| 503 | 503 | LLM服务不可用 |

---

## 3. 异步任务接口

### 3.1 POST /api/ai/tasks

创建异步任务，立即返回task_id，后台异步执行。

**请求体**：

```json
{
  "task_type": "batch_post",
  "input_data": {
    "messages": [
      "发一篇Python基础教程",
      "发一篇Python进阶教程",
      "发一篇Python实战教程"
    ],
    "section_id": 1
  },
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_type` | string | 是 | 任务类型，见下方枚举 |
| `input_data` | object | 是 | 任务输入参数，结构因task_type而异 |
| `conversation_id` | string(UUID) | 否 | 关联会话 |

**task_type枚举**：

| 值 | 说明 | input_data结构 |
|----|------|---------------|
| `single_post` | 单篇发帖 | `{message: string}` |
| `batch_post` | 批量发帖 | `{messages: string[], section_id?: int}` |
| `single_problem` | 单题生成 | `{message: string}` |
| `batch_problem` | 批量出题 | `{messages: string[]}` |

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "task_id": "770e8400-e29b-41d4-a716-446655440000",
    "task_type": "batch_post",
    "status": "pending",
    "created_at": "2026-06-01T10:00:00Z"
  }
}
```

### 3.2 GET /api/ai/tasks

查询当前用户的任务列表。

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | string | 否 | 按状态筛选 |
| `task_type` | string | 否 | 按类型筛选 |
| `page` | int | 否 | 页码，默认1 |
| `page_size` | int | 否 | 每页数量，默认20，最大50 |

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "count": 5,
    "page": 1,
    "page_size": 20,
    "results": [
      {
        "task_id": "770e8400-e29b-41d4-a716-446655440000",
        "task_type": "batch_post",
        "status": "completed",
        "agent_name": "forum",
        "created_at": "2026-06-01T10:00:00Z",
        "started_at": "2026-06-01T10:00:01Z",
        "completed_at": "2026-06-01T10:02:30Z"
      }
    ]
  }
}
```

### 3.3 GET /api/ai/tasks/{task_id}

查询单个任务的详细状态和结果。

**响应（执行中）**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "task_id": "770e8400-e29b-41d4-a716-446655440000",
    "task_type": "batch_post",
    "status": "running",
    "agent_name": "forum",
    "progress": {
      "total": 3,
      "completed": 1,
      "failed": 0
    },
    "input_data": {
      "messages": ["发一篇Python基础教程", "发一篇Python进阶教程", "发一篇Python实战教程"]
    },
    "result_data": null,
    "created_at": "2026-06-01T10:00:00Z",
    "started_at": "2026-06-01T10:00:01Z"
  }
}
```

**响应（已完成）**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "task_id": "770e8400-e29b-41d4-a716-446655440000",
    "task_type": "batch_post",
    "status": "completed",
    "agent_name": "forum",
    "progress": {
      "total": 3,
      "completed": 3,
      "failed": 0
    },
    "input_data": {
      "messages": ["发一篇Python基础教程", "发一篇Python进阶教程", "发一篇Python实战教程"]
    },
    "result_data": {
      "results": [
        {"index": 0, "status": "success", "post_id": 123, "title": "Python基础教程"},
        {"index": 1, "status": "success", "post_id": 124, "title": "Python进阶教程"},
        {"index": 2, "status": "success", "post_id": 125, "title": "Python实战教程"}
      ]
    },
    "created_at": "2026-06-01T10:00:00Z",
    "started_at": "2026-06-01T10:00:01Z",
    "completed_at": "2026-06-01T10:02:30Z"
  }
}
```

**响应（失败）**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "task_id": "770e8400-e29b-41d4-a716-446655440000",
    "task_type": "batch_post",
    "status": "failed",
    "agent_name": "forum",
    "error_message": "M3内容服务不可用: Connection refused",
    "retry_count": 3,
    "created_at": "2026-06-01T10:00:00Z",
    "started_at": "2026-06-01T10:00:01Z",
    "completed_at": "2026-06-01T10:00:45Z"
  }
}
```

### 3.4 DELETE /api/ai/tasks/{task_id}

取消正在执行或等待中的任务。

**响应**：

```json
{
  "code": 200,
  "message": "任务已取消",
  "timestamp": 1717200000000,
  "data": {
    "task_id": "770e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled"
  }
}
```

**错误响应**：

| HTTP状态码 | code | 说明 |
|-----------|------|------|
| 404 | 404 | 任务不存在 |
| 409 | 409 | 任务已完成/已取消，无法取消 |

---

## 4. 会话管理接口

### 4.1 GET /api/ai/conversations

查询当前用户的会话列表。

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | string | 否 | active/archived |
| `page` | int | 否 | 页码，默认1 |
| `page_size` | int | 否 | 每页数量，默认20 |

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "count": 10,
    "page": 1,
    "page_size": 20,
    "results": [
      {
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "发帖：Git基础命令教程",
        "status": "active",
        "message_count": 4,
        "last_message_at": "2026-06-01T10:05:00Z",
        "created_at": "2026-06-01T10:00:00Z"
      }
    ]
  }
}
```

### 4.2 GET /api/ai/conversations/{id}

查询会话详情，包含所有消息历史。

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "发帖：Git基础命令教程",
    "status": "active",
    "created_at": "2026-06-01T10:00:00Z",
    "messages": [
      {
        "message_id": "msg-001",
        "role": "user",
        "content": "在技术分享板块发一篇关于Git基础命令的教程",
        "created_at": "2026-06-01T10:00:00Z"
      },
      {
        "message_id": "msg-002",
        "role": "assistant",
        "content": "已在「技术分享」板块发布了帖子《Git基础命令教程》，帖子ID: 123。",
        "intent": "forum",
        "agent_name": "forum",
        "tool_calls": [
          {"tool_name": "list_sections", "status": "success", "duration_ms": 120},
          {"tool_name": "create_post", "status": "success", "duration_ms": 350}
        ],
        "token_usage": {"input": 1500, "output": 800},
        "created_at": "2026-06-01T10:00:05Z"
      }
    ]
  }
}
```

### 4.3 DELETE /api/ai/conversations/{id}

删除会话及其所有消息。

**响应**：

```json
{
  "code": 200,
  "message": "会话已删除",
  "timestamp": 1717200000000,
  "data": null
}
```

---

## 5. Agent管理接口

### 5.1 GET /api/ai/agents

查询所有Agent配置（仅管理员）。

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1717200000000,
  "data": [
    {
      "agent_name": "router",
      "display_name": "主路由Agent",
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.3,
      "max_tokens": 1024,
      "is_enabled": true
    },
    {
      "agent_name": "forum",
      "display_name": "论坛Agent",
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.7,
      "max_tokens": 8192,
      "is_enabled": true
    },
    {
      "agent_name": "problem",
      "display_name": "出题Agent",
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.5,
      "max_tokens": 8192,
      "is_enabled": true
    }
  ]
}
```

### 5.2 PUT /api/ai/agents/{name}

更新Agent配置（仅管理员）。

**请求体**：

```json
{
  "temperature": 0.5,
  "max_tokens": 4096,
  "is_enabled": true,
  "system_prompt": "更新后的系统提示词..."
}
```

**响应**：

```json
{
  "code": 200,
  "message": "Agent配置已更新",
  "timestamp": 1717200000000,
  "data": {
    "agent_name": "forum",
    "display_name": "论坛Agent",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.5,
    "max_tokens": 4096,
    "is_enabled": true
  }
}
```

---

## 6. 错误码定义

### 6.1 业务错误码

| HTTP状态码 | code | message | 说明 |
|-----------|------|---------|------|
| 400 | 40001 | 消息内容不能为空 | message为空 |
| 400 | 40002 | 消息长度超限 | message超过5000字符 |
| 400 | 40003 | 不支持的任务类型 | task_type无效 |
| 400 | 40004 | 任务输入参数错误 | input_data格式错误 |
| 401 | 40100 | 未认证 | 缺少X-User-Id |
| 403 | 40300 | 权限不足 | 非管理员 |
| 404 | 40401 | 会话不存在 | conversation_id无效 |
| 404 | 40402 | 任务不存在 | task_id无效 |
| 409 | 40901 | 任务无法取消 | 任务已完成/已取消 |
| 429 | 42901 | 并发任务数超限 | 同时运行任务>3 |
| 500 | 50001 | Agent执行异常 | 内部错误 |
| 503 | 50301 | LLM服务不可用 | Claude API不可达 |

### 6.2 错误响应示例

```json
{
  "code": 42901,
  "message": "并发任务数超限",
  "timestamp": 1717200000000,
  "errors": {
    "current_running": 3,
    "max_allowed": 3
  }
}
```

---

**文档维护**: 后端开发团队
**最后更新**: 2026-06-05
