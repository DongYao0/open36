# M9 - 招新管理服务技术设计文档

## 文档概述

本文件夹包含 **M9 招新管理服务 (enrollment-service)** 的技术设计文档。

**服务职责**: 招新报名、面试管理、作业分发与收集

**技术栈**: Java 17 + Spring Boot 3.x + Sa-Token + JPA + PostgreSQL

**服务端口**: 8084

---

## 服务架构

```
Open436-Admin :3001
       │ (Vite proxy: /api/enrollment, /api/interview, /api/assignment)
       ▼
  Enrollment :8084
  ├── EnrollmentController   /api/enrollment/**
  ├── InterviewController    /api/interview/**
  └── AssignmentController   /api/assignment/**
       │
       ├── PostgreSQL :55400 (open436 数据库)
       └── Redis :6380 (Sa-Token session)
```

## 数据模型

### EnrollmentApplication（招新申请）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long (PK) | 自增主键 |
| authUserId | Long | 关联 Auth 服务的用户 ID |
| username | String | 用户名 |
| realName | String | 真实姓名 |
| studentId | String | 学号 |
| phone | String | 联系方式 |
| major | String | 专业 |
| selfIntro | TEXT | 自我介绍 |
| skills | TEXT | 技能标签（逗号分隔） |
| status | String | pending/approved/rejected |
| submittedAt | DateTime | 提交时间 |
| reviewedAt | DateTime | 审核时间 |
| reviewedBy | String | 审核人 |
| reviewReason | TEXT | 审核意见 |

### Interview（面试记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long (PK) | 自增主键 |
| enrollmentId | Long | 关联申请 ID |
| round | Integer | 面试轮次 |
| score | Integer | 评分 |
| evaluator | String | 面试官 |
| feedback | TEXT | 面试反馈 |
| result | String | pass/fail/pending |
| createdAt | DateTime | 创建时间 |

### Assignment（作业任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long (PK) | 自增主键 |
| title | String | 作业标题 |
| description | TEXT | 作业描述 |
| deadline | DateTime | 截止时间 |
| createdAt | DateTime | 创建时间 |

### AssignmentAllocation（作业分配）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long (PK) | 自增主键 |
| assignmentId | Long | 关联作业 ID |
| studentId | String | 学号 |
| allocatedAt | DateTime | 分配时间 |

### AssignmentSubmission（作业提交）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long (PK) | 自增主键 |
| assignmentId | Long | 关联作业 ID |
| studentId | String | 学号 |
| content | TEXT | 提交内容 |
| submittedAt | DateTime | 提交时间 |

---

## 数据库迁移

| 版本 | 文件 | 说明 |
|------|------|------|
| V1 | `V1__create_enrollment_applications.sql` | 创建申请表 |
| V2 | `V2__add_auth_user_id.sql` | 添加 authUserId 字段 |
| V3 | `V3__drop_redundant_user_fields.sql` | 清理冗余字段 |
| V4 | `V4__create_interviews.sql` | 创建面试表 |

---

## 配置说明

**application.yml 关键配置**：

```yaml
server:
  port: 8084

spring:
  datasource:
    url: jdbc:postgresql://localhost:55400/open436
    username: open436
    password: ${DB_PASSWORD:open436}

sa-token:
  token-name: token
  timeout: 2592000
```

---

## 与其他服务的关系

| 依赖 | 说明 |
|------|------|
| Open436-Auth | 通过 authUserId 关联用户，审核通过后可调用 Auth 的激活接口 |
| PostgreSQL | 共享 open436 数据库 |
| Redis | Sa-Token session 存储 |

---

**文档版本**：v1.0
**创建日期**：2026-06-14
