# Open436 前端聚合网关

将 **3D 首页（Open436-Landing）** 与 **Vue 主应用（Open436-Frontend）** 通过 Nginx 反向代理聚合到**单一入口**，使 3D 首页成为项目根 `/`，Vue 应用挂到 `/app`。

## 路由拓扑

```
浏览器 :8080
   │
   ├─ /              → Open436-Landing   (3D 首页, Vite :5173)
   ├─ /app/          → Open436-Frontend  (Vue 主应用, Vite :3000, base=/app/)
   ├─ /api/*         → Vue dev server 的 vite proxy → 各后端微服务
   └─ /algo          → Vue dev server 的 vite proxy → HOJ(:8066)
```

> API 路由**不在此重复维护**：统一透传给 Vue dev server，由其 `vite.config.js` 的 `server.proxy` 分发到各微服务（auth/posts/files/...），保持路由表单点维护。

## 前置：启动两个前端 dev server

```bash
# 终端 1 —— 3D 首页（:5173）
cd Open436-Landing
npm install        # 首次
npm run dev

# 终端 2 —— Vue 主应用（:3000）
cd Open436-Frontend
npm install        # 首次
npm run dev
```

## 启动网关

```bash
docker compose -f deploy/dev/nginx/docker-compose.yml up -d
```

打开 **http://localhost:8080** → 看到 3D 首页；点击右上角「进入平台」→ 跳转 `/app` 进入 Vue 主应用。

## 常用命令

```bash
# 停止
docker compose -f deploy/dev/nginx/docker-compose.yml down

# 查看日志（排查代理问题）
docker compose -f deploy/dev/nginx/docker-compose.yml logs -f

# 改完 nginx.conf 后重启生效
docker compose -f deploy/dev/nginx/docker-compose.yml restart
```

## 已知限制 / 排错

| 现象 | 原因与处理 |
|------|-----------|
| 改了 `nginx.conf` 未生效 | `restart` 网关容器（配置以只读卷挂载） |
| Vue 页面 404 / 资源丢失 | 确认 `Open436-Frontend/vite.config.js` 已设 `base: '/app/'` 且 dev server 已重启 |
| 3D 模型加载失败 | 确认 `Open436-Landing` dev server 在 :5173 运行；模型用相对路径 `./desktop_pc/`，依赖根路径部署 |
| API 报错 | 检查对应后端微服务是否启动；API 链路为 Nginx → Vue proxy → 微服务 |
| Vite HMR 不热更新 | 刷新页面即可（HMR 经反代偶有不稳定，不影响功能） |
| `host.docker.internal` 无法解析 | Docker Desktop 默认支持；Linux 需确保网关配了 `host-gateway`（已配） |

## 生产部署提示

生产环境无需此 dev 网关。两端分别 `npm run build` 后：
- `Open436-Landing/dist`  → 托管于 `/`
- `Open436-Frontend/dist` → 托管于 `/app/`
- 由生产 Nginx / CDN 直接按路径分发静态资源，API 走 Kong 网关。
