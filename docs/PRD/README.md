# Open436 - PRD 产品需求文档

## 模块总览

| 编号 | 模块名称 | 服务目录 | 状态 | 说明 |
|------|---------|---------|------|------|
| **M1** | 认证与授权 | Open436-Auth | ✅ 已实现 | 用户认证、RBAC 权限、HOJ SSO |
| **M2** | 用户管理 | *(合并到 M1)* | ⚠️ 已合并 | UserProfile/UserStatistics 在 Auth 服务中 |
| **M3** | 内容管理 | Open436-Forum | ✅ 已实现 | 帖子 CRUD（Django App） |
| **M4** | 评论与互动 | Open436-Forum | ✅ 已实现 | 回复、点赞、收藏（Django App） |
| **M5** | 板块管理 | Open436-Forum | ✅ 已实现 | 板块 CRUD（Django App） |
| **M6** | 搜索与索引 | — | ❌ 未实现 | 全文搜索（Milvus 已部署，未接入） |
| **M7** | 文件存储 | Open436-FileService | ✅ 已实现 | MinIO 对象存储（FastAPI） |
| **M8** | AI 智能服务 | Open436-AIService | ✅ 已实现 | LangChain Agent（FastAPI） |
| **M9** | 招新管理 | Open436-Enrollment | ✅ 已实现 | 报名、面试、作业（Spring Boot） |
| **M10** | 内容采集 | Open436-CrawlerService | ✅ 已实现 | 爬虫 + AI 整理 + 日报（Python） |
| **M11** | HOJ 算法评测 | Open436-hoj | 🔗 集成部署 | 第三方系统，SSO 对接 |

> **说明**：
> - M2 用户管理的代码已合并到 M1 Auth 服务，PRD 和 TDD 文档保留作为需求参考。
> - M3/M4/M5 共享同一个 Django 服务（Open436-Forum），通过 App 划分职责。
> - M11 HOJ 是第三方系统，非自研，通过 SSO 集成。

---

## 服务与模块映射

```
Open436-Auth (:8081)          → M1 认证与授权 + M2 用户管理
Open436-Forum (:8003)         → M3 内容管理 + M4 评论互动 + M5 板块管理
Open436-FileService (:8007)   → M7 文件存储
Open436-AIService (:8008)     → M8 AI 智能服务
Open436-Enrollment (:8084)    → M9 招新管理
Open436-CrawlerService        → M10 内容采集
Open436-hoj (:6688/8066)      → M11 HOJ 算法评测
```

---

## 文档目录

| 文档 | 路径 |
|------|------|
| M1 认证与授权 | [M1-认证与授权模块.md](M1-认证与授权模块.md) |
| M2 用户管理 | [M2-用户管理模块.md](M2-用户管理模块.md) |
| M3 内容管理 | [M3-内容管理模块.md](M3-内容管理模块.md) |
| M4 评论与互动 | [M4-评论与互动模块.md](M4-评论与互动模块.md) |
| M5 板块管理 | [M5-板块管理模块.md](M5-板块管理模块.md) |
| M6 搜索与索引 | [M6-搜索与索引模块.md](M6-搜索与索引模块.md) |
| M7 文件存储 | [M7-文件存储模块.md](M7-文件存储模块.md) |
| M8 AI 智能服务 | [M8-AI智能服务模块.md](M8-AI智能服务模块.md) |
| M9 招新管理 | [M9-招新管理模块.md](M9-招新管理模块.md) |
| M10 内容采集 | [M10-内容采集模块.md](M10-内容采集模块.md) |

---

**最后更新**：2026-06-14
