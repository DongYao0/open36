# HOJ 在线判题系统修复报告

> 项目：Open436 教育平台  
> 模块：HOJ (Hcode Online Judge) 在线判题子系统  
> 修复周期：2026-06-03 ~ 2026-06-04  
> 状态：**已修复，全链路验证通过**

---

## 一、问题背景

Open436 平台集成了 HOJ 在线判题系统，用于编程题目的自动评测。HOJ 采用三层架构：

```
用户 → hoj-vue (前端:8066) → hoj-backend (后端:6688) → hoj-judge (判题机:8088) → go-judge (沙箱:5050)
```

系统在 Docker Compose 中以 `--profile hoj` 可选模式部署。在修复前，HOJ 处于**完全不可用**状态：

- 前端"在线测试"和"提交测评"按钮置灰不可点击
- 所有历史提交记录状态为 `System Error`（status=10）或 `Pending`（status=5）
- 判题服务器无法连接沙箱服务
- 无任何一道题目能够完成判题

---

## 二、问题排查与修复过程

### 2.1 go-judge 沙箱启动失败

**现象**：go-judge 容器启动后立即退出，日志报错：

```
mkdir /sys/fs/cgroup/cpu/gojudge: read-only file system
```

**根因**：go-judge 需要操作 cgroup 文件系统来实现资源限制（CPU/内存），但容器默认以非特权模式运行，无法写入 `/sys/fs/cgroup`。

**修复**：在 `docker-compose.yml` 中为 go-judge 添加 `privileged: true`：

```yaml
go-judge:
  privileged: true
```

---

### 2.2 Docker 镜像不可用

**现象**：构建 hoj-backend 和 hoj-judge 的 Docker 镜像时失败：

```
manifest for openjdk:8-jre-slim not found
manifest for maven:3.8-openjdk-8 not found
```

**根因**：Docker Hub 上的 `openjdk:8-jre-slim` 和 `maven:3.8-openjdk-8` 镜像已被官方下架（Oracle JDK 许可变更）。

**修复**：修改 `Dockerfile.backend` 和 `Dockerfile.judge`，替换基础镜像：

| 原镜像 | 替换为 |
|--------|--------|
| `maven:3.8-openjdk-8` | `maven:3.8-eclipse-temurin-8` |
| `openjdk:8-jre-slim` | `eclipse-temurin:8-jre` |

---

### 2.3 判题服务器 MySQL 连接失败

**现象**：hoj-judge 启动时报错，无法连接 MySQL：

```
Communications link failure
Connection refused: hoj-mysql:3306
```

**根因**：hoj-judge 的 `application.yml` 中数据源 URL 使用了自定义占位符 `${hoj.db.public-host:172.20.0.3}`，默认值指向旧网段 IP `172.20.0.3`，而 Docker 网络重建后子网已变为 `172.28.0.0/16`。

**修复**：
1. 在 docker-compose.yml 中添加环境变量覆盖默认值：

```yaml
hoj-judge:
  environment:
    HOJ_DB_PUBLIC_HOST: hoj-mysql
    HOJ_DB_PUBLIC_PORT: "3306"
    HOJ_DB_NAME: hoj
```

2. 为 hoj-mysql 添加健康检查，hoj-judge 添加启动依赖：

```yaml
hoj-mysql:
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p${HOJ_MYSQL_PASS:-hoj123456}"]
    interval: 5s
    timeout: 5s
    retries: 10

hoj-judge:
  depends_on:
    hoj-mysql: { condition: service_healthy }
    go-judge: { condition: service_started }
```

---

### 2.4 Sandbox URL 字节码硬编码（核心问题）

**现象**：判题服务器启动正常，`/version` 接口返回成功，但实际提交后报错：

```
Cannot connect to sandbox service.
I/O error on DELETE request for "http://localhost:5050/file/xxx": Connection refused
```

**根因**：JudgeServer 的 JAR 包中 `SandboxRun.class` 有**两处** URL 硬编码：

| 位置 | 原始值 | 用途 |
|------|--------|------|
| 常量池偏移 5932 | `http://localhost:5050` | 沙箱请求基础 URL |
| 常量池偏移 6358 | `http://localhost:5050/file/{0}` | 文件清理 URL |

源码虽有 `System.getenv().getOrDefault("SANDBOX_URL", "http://localhost:5050")`，但 Docker 镜像基于旧版源码构建，编译后的字节码直接硬编码了 `http://localhost:5050`，**不读取环境变量**。

而 Docker 网络会拦截 `localhost` 的 DNS 解析，使其始终指向容器自身（127.0.0.1），而非 go-judge 容器。无论怎么修改 `/etc/hosts` 都无法覆盖。

**修复**：编写 Python 脚本对 JAR 进行二进制 patch，替换字节码中的 URL：

```python
replacements = [
    (b'http://localhost:5050/file/{0}', b'http://judgehost:5050/file/{0}'),
    (b'http://localhost:5050', b'http://judgehost:5050'),
]
```

选择 `judgehost` 而非 `go-judge` 作为主机名的原因：Docker DNS 会拦截 `localhost` 解析，但**不会拦截自定义主机名**。通过在容器 entrypoint 中动态写入 `/etc/hosts` 实现解析：

```yaml
entrypoint: ["/bin/sh", "-c",
  "GOJIP=$$(getent hosts go-judge | awk '{print $$1}') &&
   if [ -n \"$$GOJIP\" ]; then echo \"$$GOJIP judgehost\" >> /etc/hosts; fi &&
   exec java -jar app.jar"]
```

**注意事项**：
- Spring Boot 嵌套 JAR 必须以 `ZIP_STORED`（非压缩）方式存储，否则启动时报 `Unable to open nested entry` 错误
- 同长度替换（`localhost` 和 `judgehost` 均为 9 字符）无需修改字节码偏移量
- JAR 通过 volume 挂载到容器：`./hoj-judge-app.jar:/app/app.jar`

---

### 2.5 测试用例文件跨容器不可见（最终阻塞点）

**现象**：编译通过，但执行阶段报错：

```
pipe: open file /judge/test_case/problem_1000/1.in:
      open /judge/test_case/problem_1000/1.in: no such file or directory
```

提交记录状态为 `System Error`（status=4）。

**根因**：HOJ 判题流程中，JudgeServer 在首次判题时从数据库读取测试用例，写入本地文件系统 `/judge/test_case/problem_{id}/`。随后调用 go-judge 时，通过 `PreparedFile` 的 `src` 字段将文件路径传给沙箱：

```java
// SandboxRun.java:333
testCaseInput.set("src", testCasePath);  // → /judge/test_case/problem_1000/1.in
```

go-judge 的 `src` 机制要求文件存在于**沙箱自身的文件系统**中。但 go-judge 运行在独立容器内，无法访问 hoj-judge 容器的 `/judge/test_case/` 目录。

**修复**：在 docker-compose.yml 中添加共享 volume，使两个容器挂载同一目录：

```yaml
go-judge:
  volumes: [hoj-testcase:/judge/test_case]

hoj-judge:
  volumes:
    - ./hoj-judge-app.jar:/app/app.jar
    - hoj-testcase:/judge/test_case

volumes:
  hoj-testcase:
```

**工作流程**：
1. hoj-judge 收到判题请求 → 从 MySQL 读取测试用例 → 写入 `/judge/test_case/problem_{id}/`
2. hoj-judge 向 go-judge 发送编译+运行请求，`src` 指向 `/judge/test_case/problem_{id}/1.in`
3. go-judge 通过共享 volume 读取文件 → 执行 → 返回结果
4. hoj-judge 比较输出 → 更新数据库状态

---

## 三、其他问题

### 3.1 前端按钮置灰

**现象**：前端"在线测试"和"提交测评"按钮始终置灰。

**根因**：`judge_server` 表中判题服务器记录的 `task_number` 已满或服务未正确注册。每次 hoj-judge 重启会重新注册（删除旧记录、插入新记录），但按钮状态依赖后端对判题服务器的可用性判断。

**状态**：随着上述核心问题修复，判题服务器正常注册后自动恢复。

### 3.2 API 提交参数格式

**现象**：通过 API 提交代码时返回各种错误。

**注意事项**：
- `pid` 字段应使用 `problem_id`（如 "12"），而非数据库 `id`（如 1000）
- `cid` 字段不能省略，非比赛提交设为 `0`
- `language` 字段使用中文名（如 "C"、"C++"、"Python3"），非编译器版本号
- 代码长度需 >= 50 字符（Python/PHP/Ruby/Rust/JavaScript 除外）
- C/C++ 代码中 `\n` 等转义序列需确保到达沙箱时为字面量反斜杠+n，而非实际换行符

---

## 四、最终验证

### 4.1 端到端测试

```
提交代码（C语言，读取整数并输出）
→ 后端接收 (submitId=17, status=5 Pending)
→ 判题服务器从数据库加载测试用例 → 写入共享 volume
→ 编译请求发送至 go-judge → 编译成功
→ 运行请求发送至 go-judge → 执行成功
→ 输出比对 → 匹配
→ status=0 Accepted, memory=284KB
```

### 4.2 各组件状态

| 组件 | 容器名 | 端口 | 状态 |
|------|--------|------|------|
| go-judge 沙箱 | go-judge | 5050 | v1.12.0 运行正常 |
| hoj-judge 判题机 | open436-hoj-judge | 8088 | 已注册，沙箱已连接 |
| hoj-backend 后端 | open436-hoj-backend | 6688 | 运行正常 |
| hoj-vue 前端 | open436-hoj-vue | 8066 | 运行正常 |
| hoj-mysql 数据库 | open436-hoj-mysql | 3308 | 健康检查通过 |

### 4.3 判题服务器注册

```sql
SELECT id, name, ip, port, status, is_remote, max_task_number
FROM judge_server;
-- id=27  hoj-judger-1  open436-hoj-judge  8088  status=0(可用)  is_remote=0  max_task=33
-- id=28  hoj-judger-1  open436-hoj-judge  8088  status=0(可用)  is_remote=1  max_task=65
```

---

## 五、修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `docker-compose.yml` | go-judge 添加 `privileged: true`、共享 volume；hoj-judge 添加环境变量、depends_on、volume；hoj-mysql 添加 healthcheck；添加 `hoj-testcase` volume 声明 |
| `Open436-hoj/hoj-springboot/Dockerfile.judge` | 基础镜像改为 `eclipse-temurin:8-jre` |
| `Open436-hoj/hoj-springboot/Dockerfile.backend` | 基础镜像改为 `eclipse-temurin:8-jre` |
| `hoj-judge-app.jar` | 二进制 patch SandboxRun.class 中两处 `localhost:5050` → `judgehost:5050` |
| `patch_jar.py` | JAR 二进制 patch 脚本（工具文件） |

---

## 六、经验总结

1. **Docker 网络的 localhost 陷阱**：Docker 会拦截容器内 `localhost` 的 DNS 解析，使其指向容器自身。修改 `/etc/hosts` 对 `localhost` 无效，需使用自定义主机名。

2. **JAR 字节码与源码不一致**：Docker 镜像中的 JAR 可能基于旧版源码构建。环境变量读取逻辑（`System.getenv()`）在源码中存在但编译产物中缺失，需通过字节码分析确认。

3. **跨容器文件共享**：当一个容器需要读取另一个容器产生的文件时，Docker named volume 是最简洁的方案。需注意 volume 的首次写入时序。

4. **Spring Boot 嵌套 JAR 的 ZIP 格式**：Spring Boot 的 fat JAR 内部使用 `ZIP_STORED`（非压缩）存储嵌套 JAR。任何修改 fat JAR 的工具都必须保持此格式，否则启动失败。

5. **端到端验证的重要性**：仅检查组件健康状态（`/version` 接口）不足以发现深层问题。必须通过实际提交代码并获取判题结果来验证完整链路。
