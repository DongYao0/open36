# ── HOJ Vue ── Node 18 构建 + Nginx
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci --legacy-peer-deps
COPY . .
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npx vue-cli-service build

FROM nginx:1.27-alpine
RUN apk add --no-cache curl
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
  CMD curl -fsS http://localhost:80/algo/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
