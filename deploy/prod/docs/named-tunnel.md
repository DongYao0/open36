# Cloudflare Named Tunnel 切换指南（阶段12）

> 状态：**人工基础设施步骤，未执行**。Quick Tunnel 不能承载千人正式流量
> （官方限制 200 并发 in-flight、不支持 SSE、URL 随机轮换）。
> 本文档是执行清单；代码侧（compose Token 注入）已就绪。

## 1. 前置采购

1. 购买一个域名（任何注册商，年费 ~¥60）。
2. 将域名 DNS 托管到 Cloudflare（免费计划即可）。

## 2. 创建 Named Tunnel

1. 打开 https://one.dash.cloudflare.com → Networks → Tunnels。
2. Create a tunnel → 选择 Cloudflared → 命名 `open436-prod`。
3. 记下安装命令中的 Token（形如 `eyJh...` 长串）。

## 3. 绑定 Public Hostname

| Subdomain | Domain | Service |
|---|---|---|
| www（或 @） | 你的域名 | `http://public-web:80` |

Tunnel 与 public-web 在同一 Docker 网络，用服务名直连。

## 4. 服务器配置（真实 .env，不入 Git）

```bash
# /home/sunrise-ssh/open436/deploy/prod/.env.production
CLOUDFLARE_TUNNEL_TOKEN=eyJh...（你的 Token）
```

重启隧道：

```bash
cd ~/open436/deploy/prod
docker compose --env-file .env.production -f compose.yml \
  --profile tunnel up -d cloudflared
docker logs open436-prod-cloudflared   # 确认 registered + 协议 http2
```

未配置 Token 时自动回退 Quick Tunnel（日志有明确提示）。

## 5. Cloudflare 缓存规则（关键）

### 允许边缘缓存（Cache Rules → Cache Eligible）

- `www.域名/assets/*`（Landing 哈希资产）
- `www.域名/app/assets/*`（Vue 哈希资产）
- `www.域名/honors/*`（荣誉相册图片）
- `www.域名/objects/open436-posts/*`（论坛公开图片，仅公共 bucket）

Edge TTL 跟随源站 Cache-Control（已配置 immutable 1 年 / 7 天+SWR）。

### 绕过缓存（Bypass cache，逐条列出）

- `www.域名/api/auth/*`（登录/注册/Token）
- `www.域名/api/enrollment/*`（报名提交）
- `www.域名/api/users/homepage/admin/*`（管理端）
- `www.域名/api/ai/*`（SSE 流式——Quick Tunnel 不支持 SSE 的根因，
  Named Tunnel 下也必须绕过缓存才能流式）
- `www.域名/api/*` 其余全部（默认 no-store，不逐条配置也可，
  但禁止对 /api/* 使用 "Cache Everything"）
- `www.域名/app/*` 非 assets 路径（用户中心 SPA，含登录态）
- `www.域名/algo/*` 动态部分（HOJ 提交与用户状态接口）

### 绝对禁止

- 对 `*/api/*` 设置 Cache Everything——会把带 Token 的私有响应缓存到边缘。

## 6. 验收清单

- [ ] 域名 HTTPS 打开首页，证书正常
- [ ] `/api/users/homepage/public` 响应头 `Cache-Control: public, max-age=60`
- [ ] 登录/报名 POST 不命中 CF 缓存（DevTools 看 cf-cache-status: BYPASS/DYNAMIC）
- [ ] AI 流式对话逐字输出（SSE 通畅）
- [ ] 1000 人压测（LAN 8080 直连 + 隧道各跑一遍，对比吞吐）
- [ ] 重启 cloudflared 容器，域名不变

## 7. 回滚

真实 .env 清空 `CLOUDFLARE_TUNNEL_TOKEN` 并重启 cloudflared
→ 回退 Quick Tunnel（临时 URL，需重新分发）。
