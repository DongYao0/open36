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
- HOJ 判题队列 >100 持续 5 分钟
- HOJ 判题 rejected >0（立即，critical）

## Grafana 看板

Data Source → Prometheus → `http://prometheus:9090`。
推荐导入社区看板：1860（Node）、14282（cAdvisor）、9628（PostgreSQL），
再为 `poolQueued/poolRejected` 手工建 HOJ 面板。

## 已知跟进项（诚实范围声明）

- API 5xx 比例与 P95 延迟告警需要网关侧 metrics：
  Kong 开启 prometheus 插件（KONG_PLUGINS 增加 prometheus，
  再在 kong.yml 路由挂 plugin）或 nginx-stub 日志统计；
  接入后在此文件补两条规则即可。
- 告警通知渠道（邮件/webhook）未配置——当前仅 Prometheus UI 可见，
  生产化前接入 Alertmanager。
