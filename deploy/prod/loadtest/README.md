# Open436 压测工具（k6）

> 阶段1交付物。原则：**先建立可复现的测量，再谈优化**。
> "1000 人在线" ≠ "1000 rps"：所有浏览场景都带 3~8 秒随机停顿。

## 环境

- 压测电脑与 Linux 主机都连接 **天元 5G**；
- Linux 上叠加压测端口（临时，勿提交到正式 compose）：

```bash
cd deploy/prod
docker compose --env-file .env.production \
  -f compose.yml -f loadtest/compose.loadtest.yml up -d public-web
```

- 压测电脑安装 k6（`choco install k6` / `brew install k6` / 官方包）；
- 统一入口 `http://172.20.193.162:8080`，绕过 Quick Tunnel 200 并发限制。

## 场景

| 文件 | 场景 | 命令 |
|---|---|---|
| browse.js | A：0→200→500→1000 VU 爬坡，保持10分钟 | `k6 run -e BASE_URL=http://172.20.193.162:8080 browse.js` |
| forum-read.js | B：300 并发，80%列表/20%详情+回复 | `k6 run -e BASE_URL=... forum-read.js`（`-e POST_ID_MAX=实际最大帖子id`） |
| enrollment.js | C：报名 20/100/300 并发+幂等验证 | `k6 run -e BASE_URL=... -e TIER=20 enrollment.js`（TIER=100 / 300） |
| admin-read.js | 管理端 200 只读 | `k6 run -e ADMIN_URL=http://172.20.193.162:3001 -e ADMIN_USER=.. -e ADMIN_PASS=.. admin-read.js` |
| hoj-submit.js | D：150浏览 + 20提交/s×3min | `k6 run -e BASE_URL=... -e HOJ_ACCOUNTS="u1:p1,u2:p2,..." hoj-submit.js` |

## HOJ 压测账号准备（场景D前置）

HOJ 单用户提交间隔 8s（defaultSubmitInterval），20 提交/秒需要 ≥50 个账号。
用 root 管理员在 HOJ 后台批量创建 `ltc1..ltc60`（或用注册接口脚本），
格式 `HOJ_ACCOUNTS="ltc1:pass,ltc2:pass,..."` 传入。**密码只放本地环境变量，不入库不入仓。**

## 验收线（判定通过/失败）

| 指标 | 阈值 |
|---|---|
| 静态资源失败率 | < 0.1% |
| 动态 API 失败率 | < 1% |
| 普通查询 P95 / P99 | < 800ms / < 2000ms |
| 报名提交 P95 | < 2000ms |
| 服务 OOM / 反复重启 | 不允许 |
| PG / MySQL 连接使用率 | 长期 < 80% |
| HOJ 提交丢失（hoj_submit_lost） | = 0 |
| 过载响应 | 明确 429/503，不得无限卡住 |

## 报名幂等性验证（阶段5验收）

enrollment.js 每用户用同一 `X-Idempotency-Key` 提交 3 次 + 1 次内容漂移提交：

- `enroll_half_success` > 0 → 存在半成功账号（改造前预期为红）；
- 三次响应一致且只建一个 Auth 用户/一条申请（改造后）；
- 内容漂移提交必须 409。

服务端对账 SQL（压测后人工核对）：

```sql
-- Auth：前缀用户应与 enrollment.js 唯一迭代数一致，且无重复
SELECT username, count(*) FROM user_auth
WHERE username LIKE 'lt%' GROUP BY username HAVING count(*) > 1;

-- Enrollment：报名记录数应等于不同幂等键数
SELECT count(*), count(distinct idempotency_key) FROM enrollment_application
WHERE username LIKE 'lt%';
```

## HOJ 判题完整性验证（场景D后）

```sql
-- 所有压测提交必须到达终态（status 不应长期停留 5/6/7/9）
SELECT status, count(*) FROM judge
WHERE username LIKE 'ltc%' AND submit_time > NOW() - INTERVAL 1 DAY
GROUP BY status;
```

## 清理（压测后必须执行）

所有测试数据带 `lt` / `LT` / `ltc` 前缀。清理脚本只按前缀删除，
**只允许删除测试前缀账号，绝不触碰真实用户**：

```bash
# HOJ：ltc* 用户及其提交（root 登录后台或直接 SQL）
# Auth/Enrollment：lt* 前缀账号（见下）
```

```sql
-- 先查后删，人工确认行数与压测规模一致再执行
DELETE FROM enrollment_application WHERE username LIKE 'lt%';
DELETE FROM user_auth WHERE username LIKE 'lt%';
-- HOJ
DELETE FROM judge WHERE username LIKE 'ltc%';
DELETE FROM user_info WHERE username LIKE 'ltc%';
```

## 压测证据留存

每次压测保留：k6 summary JSON（脚本自动输出 `*-summary.json`）、
`docker stats --no-stream` 快照、数据库连接峰值、慢查询样本、HOJ 队列曲线。
目录建议：`loadtest/results/YYYYMMDD-场景名/`（results/ 不入库）。

## 结束压测

```bash
cd deploy/prod
docker compose --env-file .env.production -f compose.yml up -d public-web  # 移除8080绑定
```
