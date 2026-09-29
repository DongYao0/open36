# 监控栈（profile: monitoring）

## 启动

```bash
cd deploy/prod
docker compose --env-file .env.production -f compose.yml \
  --profile monitoring up -d
```

- Prometheus: `http://172.20.193.162:9090`（Alerts 页面查看触发的告警）
- Grafana: `http://172.20.193.162:3002`（首登 admin / ${GRAFANA_ADMIN_PASSWORD}，**改密后再用**）

端口只绑定 `ADMIN_BIND_IP`（实验室 LAN），不经 Cloudflare 暴露公网。

## 采集范围

| 来源 | 内容 |
|---|---|
| node-exporter | 主机 CPU/内存/磁盘/网络 |
| cAdvisor | 每容器 CPU/内存 |
| cloudflared `/metrics` | 公网与管理端隧道活跃连接数、QUIC RTT、重连情况 |
| blackbox-exporter | 从服务器公网出口探测首页与 HOJ `/algo/` |
| postgres-exporter | PG 活动连接/慢查询基础指标 |
| mysqld-exporter | MySQL 连接/缓冲池 |
| redis-exporter | Redis 内存/命中率/拒绝写 |
| json-exporter → hoj-judge /version | 判题池 active/queued/completed/rejected |

## 内置告警（alerts.yml）

- 磁盘剩余 <20%（10 分钟）
- PG 活动连接 >80%（150 预算）
- MySQL 活动连接 >80%（120 预算）
- Redis 内存 >90%（2GB，noeviction 写满会报错）
- 服务 up 抖动：1 小时掉线 ≥4 次（容器反复重启的代理指标）
- 服务持续 down 2 分钟
- 公网 cloudflared 指标不可达 30 秒
- 公网隧道活跃连接少于 4 条持续 30 秒、全部断开持续 15 秒
- 首页或 HOJ 公网入口不可用 30 秒、延迟超过 3 秒持续 2 分钟
- HOJ 判题队列 >100 持续 5 分钟
- HOJ 判题 rejected >0（立即，critical）

## Grafana 看板

Data Source → Prometheus → `http://prometheus:9090`。
推荐导入社区看板：1860（Node）、14282（cAdvisor）、9628（PostgreSQL），
再为 `poolQueued/poolRejected` 手工建 HOJ 面板。

## 验证

启动 `tunnel` 与 `monitoring` profile 后，在 Prometheus → Status → Targets
确认 `cloudflared`、`public-endpoint` 均为 UP。公网目标文件由 cloudflared
写入 `tunnel-runtime`，Named Tunnel 使用 `PUBLIC_CLIENT_URL`，Quick Tunnel
则在识别到随机 URL 后自动更新，无需在 Prometheus 中重复配置域名。

## 已知跟进项（诚实范围声明）

- API 5xx 比例与 P95 延迟告警需要网关侧 metrics：
  Kong 开启 prometheus 插件（KONG_PLUGINS 增加 prometheus，
  再在 kong.yml 路由挂 plugin）或 nginx-stub 日志统计；
  接入后在此文件补两条规则即可。
- 告警通知渠道（邮件/webhook）尚未配置，当前告警会在 Prometheus UI 中
  留痕；接入 Alertmanager 需要一个实际通知目标。
