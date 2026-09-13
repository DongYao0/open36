# ─────────────────────────────────────────────────────────────
#  go-judge 沙箱（可复现构建）
#
#  基础 = 官方发布镜像 criyle/go-judge:v1.12.0（已固定 tag，digest 见 README），
#  之上安装 HOJ language.yml 真正需要的运行时（与 language.yml 100% 对齐）。
#
#  language.yml 中 C / C++ / Java / Python3 / PHP / Ruby / Node / Go 均安装；
#  PyPy2 / PyPy3 / Rust / C# 未安装——从 language.yml 删除避免判题失败。
#
#  基础镜像 criyle/go-judge:v1.12.0 基于 Debian trixie（rootfs）；
#  apt 软链不可靠，必须显式调用 apt-get。
# ─────────────────────────────────────────────────────────────

FROM criyle/go-judge:v1.12.0@sha256:3af6806b4f58deeecb0cc64a8cde04138106372abfe8e6dd7acb525c3aee2e14

USER root

# 升级源 + 安装生产所需编译器 + healthcheck 工具
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3 \
        python3-pip \
        php-cli \
        ruby \
        nodejs \
        npm \
        openjdk-21-jdk-headless \
        golang-go \
        curl \
        ca-certificates \
        tini \
    && rm -rf /var/lib/apt/lists/*

# /opt/go-judge 已是 criyle/ 提供，无需覆盖
# 使用 tini 收僵尸进程（go-judge 是单进程）
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/go-judge"]

USER root
