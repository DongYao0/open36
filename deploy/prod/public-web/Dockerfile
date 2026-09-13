# ─────────────────────────────────────────────────────────────
#  Open436 public-web —— 统一对外入口（多阶段构建）
#  产物：
#    /            → Open436-Landing 静态页（3D 首页）
#    /app/*       → Open436-Frontend（Vue 业务应用）
#    /api/*       → Kong（统一网关，按前缀投递）
#    /algo/*      → HOJ 前端（算法平台）
#    /objects/*   → MinIO 对象公共读取（FileService 同源相对 URL）
#    /honors/*    → Landing 荣誉相册静态资源
#
#  仅发布容器内 80 端口；对外由 Cloudflare Quick Tunnel（profile: tunnel）访问。
#  构建上下文 = 仓库根（deploy/prod/compose.yml 已配置 `context: ../..`）。
# ─────────────────────────────────────────────────────────────

# ── 阶段 1：构建 Landing（React）──
FROM node:20-alpine AS landing-builder
WORKDIR /build/landing
COPY Open436-Landing/package*.json ./
RUN npm ci --legacy-peer-deps
COPY Open436-Landing ./
RUN npm run build

# ── 阶段 2：构建 Frontend（Vue，base=/app/）──
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend
COPY Open436-Frontend/package*.json ./
RUN npm ci
COPY Open436-Frontend ./
RUN npm run build

# ── 阶段 3：Nginx 聚合分发 ──
FROM nginx:1.27-alpine
# healthcheck 工具（alpine busybox 默认无 curl）
RUN apk add --no-cache curl
# 复制 Landing / Frontend 构建产物
COPY --from=landing-builder  /build/landing/dist  /usr/share/nginx/html/landing
COPY --from=frontend-builder /build/frontend/dist /usr/share/nginx/html/frontend
# 重要：build context 为仓库根；本 nginx.conf 必须用完整相对路径
COPY deploy/prod/public-web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
  CMD curl -fsS http://localhost:80/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]