# ── Open436 Kong（含 satoken-auth 自定义插件）──
# 固定基础镜像；插件烘焙进镜像（非运行时挂载），构建产物可审计、可复现。
FROM kong:3.4

USER root
COPY satoken-auth /usr/local/share/lua/5.1/kong/plugins/satoken-auth
USER kong

# 插件在 KONG_PLUGINS 环境变量中启用（compose 传入 bundled,satoken-auth）
