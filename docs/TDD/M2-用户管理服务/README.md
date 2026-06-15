# M2 - 用户管理服务技术设计文档

> ⚠️ **合并说明**：本模块的代码实现已合并到 M1 认证与授权服务（Open436-Auth）中。
> UserProfile、UserStatistics 实体及 Internal API 均在 Auth 服务内实现。
> 本文档保留作为早期设计参考，当前实现请参阅 [M1 TDD](../M1-认证与授权服务/)。

## 文档概述

本文件夹包含 **M2 用户管理服务** 的早期技术设计文档。

**原始职责**: 用户业务信息管理、个人资料、用户统计数据、活动历史

**当前状态**: 已合并到 Open436-Auth（Spring Boot），不再作为独立服务

---

## 📚 文档列表

| 文档                                         | 说明                                 | 状态      |
| -------------------------------------------- | ------------------------------------ | --------- |
| [00-开发指南](./00-开发指南.md)              | 开发环境搭建、项目结构、开发规范     | ✅ 已完成 |
| [01-数据库设计](./01-数据库设计.md)          | 数据库表结构、索引、关系设计         | ✅ 已完成 |
| [02-API 接口设计](./02-API接口设计.md)       | RESTful API 详细设计                 | ✅ 已完成 |
| [03-Django 模型设计](./03-Django模型设计.md) | Django Models、Serializers、ViewSets | ✅ 已完成 |
| [04-与 M1 服务集成](./04-与M1服务集成.md)    | 用户账号创建流程、服务间通信         | ✅ 已完成 |

---

## 🎯 快速导航

### 新开发者入门

1. **阅读开发指南** - 搭建开发环境
2. **阅读数据库设计** - 了解数据模型
3. **阅读 Django 模型设计** - 理解 ORM 设计
4. **阅读 API 接口设计** - 了解对外接口
5. **阅读与 M1 集成方案** - 理解服务协作

### 核心技术栈

- **语言**: Python 3.11+
- **框架**: Django 4.2+ (Django REST Framework 3.14+)
- **数据库**: PostgreSQL 14+
- **ORM**: Django ORM
- **API 文档**: drf-spectacular (OpenAPI 3.0)

---

## 🔑 核心功能

### 用户资料管理

- ✅ 查看用户信息（资料 + 统计数据）
- ✅ 编辑个人资料（昵称、头像、简介）
- ✅ 昵称修改频率限制（30 天一次）
- ✅ 头像上传（集成 M7 文件存储服务）

### 用户活动历史

- ✅ 查看用户发帖历史
- ✅ 查看用户回复历史
- ✅ 分页查询和排序

### 用户统计数据

- ✅ 发帖数统计
- ✅ 回复数统计
- ✅ 获赞数统计
- ✅ 获收藏数统计
- ✅ 实时更新统计数据

### 管理员功能

- ✅ 创建用户（配合 M1 创建认证账号）
- ✅ 编辑用户资料
- ✅ 查看用户列表
- ✅ 搜索和筛选用户

---

## 📊 数据模型概览

```
users_profile (用户资料表)
├── user_id (主键，关联 M1 的 users_auth.id)
├── nickname (昵称)
├── avatar_url (头像 URL)
├── bio (个人简介)
├── nickname_updated_at (昵称最后修改时间)
└── created_at, updated_at

user_statistics (用户统计表)
├── user_id (主键，外键)
├── posts_count (发帖数)
├── replies_count (回复数)
├── likes_received (获赞数)
├── favorites_received (获收藏数)
└── updated_at
```

---

## 🔗 模块依赖关系

### 依赖的服务

- **M1 认证授权服务**: 创建用户账号、验证用户身份
- **M7 文件存储服务**: 上传用户头像

### 被依赖的服务

- **M3 内容管理服务**: 调用获取用户信息
- **M4 互动评论服务**: 调用获取用户信息、更新统计数据

---

## 📡 服务间通信

### 调用 M1 服务

```python
# 创建用户时，先调用 M1 创建认证账号
POST http://auth-service:8001/api/auth/users
{
    "username": "alice",
    "password": "password123",
    "role": "user"
}
```

### 提供给其他服务的接口

```python
# M3、M4 调用获取用户信息
GET http://user-service:8002/api/users/{user_id}

# M4 调用更新统计数据
POST http://user-service:8002/internal/users/{user_id}/stats/increment
{
    "field": "posts_count",
    "value": 1
}
```

---

## 🗂️ 项目结构

```
user-service/
├── manage.py                    # Django 管理脚本
├── requirements.txt             # Python 依赖
├── config/                      # 配置文件
│   ├── settings.py             # Django 设置
│   ├── urls.py                 # 全局路由
│   └── wsgi.py
├── apps/
│   ├── users/                  # 用户管理应用
│   │   ├── models.py           # 数据模型
│   │   ├── serializers.py      # DRF 序列化器
│   │   ├── views.py            # 视图集
│   │   ├── urls.py             # 路由
│   │   ├── permissions.py      # 权限控制
│   │   ├── services.py         # 业务逻辑
│   │   └── tasks.py            # 异步任务
│   └── core/                   # 核心工具
│       ├── middleware.py       # 中间件
│       ├── exceptions.py       # 异常处理
│       └── utils.py            # 工具函数
├── tests/                      # 测试
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
└── docs/                       # API 文档
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

```bash
# 编辑 config/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'user_db',
        'USER': 'open436',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 3. 执行迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户

```bash
python manage.py createsuperuser
```

### 5. 运行开发服务器

```bash
python manage.py runserver 8002
```

---

## 📖 API 文档

### 访问 Swagger UI

```
http://localhost:8002/api/docs/
```

### 访问 ReDoc

```
http://localhost:8002/api/redoc/
```

---

## 🧪 测试

### 运行所有测试

```bash
python manage.py test
```

### 运行特定测试

```bash
python manage.py test apps.users.tests.test_models
```

### 测试覆盖率

```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # 生成 HTML 报告
```

---

## 🔧 性能优化

### 1. 数据库查询优化

- 使用 `select_related()` 和 `prefetch_related()` 减少查询次数
- 添加合适的数据库索引
- 使用 `only()` 和 `defer()` 控制查询字段

---

## 📦 部署

### Docker 部署

```bash
# 构建镜像
docker build -t user-service:latest .

# 运行容器
docker run -d \
  -p 8002:8002 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/user_db \
  user-service:latest
```

### 使用 docker-compose

```bash
docker-compose up -d
```

---

## 🔗 相关文档

- [PRD - M2 用户管理模块](../../PRD/M2-用户管理模块.md)
- [全局架构设计](../00-全局架构/01-全局架构设计.md)
- [服务间通信规范](../00-全局架构/03-服务间通信规范.md)
- [Django 官方文档](https://docs.djangoproject.com/)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)

---

**服务端口**: 8002  
**技术栈**: Python + Django + Django REST Framework + PostgreSQL  
**优先级**: P0（最高优先级）
