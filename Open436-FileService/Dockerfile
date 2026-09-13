# ─────────────────────────────────────────────────────────────
#  Open436 FileService —— 多阶段构建（SQLx 离线模式）
#
#  关键点：
#  1) 使用 rust:1.85.0-bookworm（与 .sqlx/ 生成时一致的 rustc 版本）；
#     如升级 rust ≥ 1.88，需同步在 .sqlx 生成环境验证。
#  2) .sqlx/ 离线元数据 + Cargo.lock 必须提交仓库；干净 Linux 环境无需
#     数据库即可编译（SQLX_OFFLINE=true，query!/query_as! 宏只查 .sqlx/）。
#  3) 生成 / 更新 .sqlx：bash deploy/prod/scripts/gen-sqlx-offline.sh
# ─────────────────────────────────────────────────────────────

FROM rust:1.85.0-bookworm AS builder

WORKDIR /app

# crates.io 镜像（国内网络直连 crates.io SSL 不稳定，走字节 rsproxy）
RUN mkdir -p /usr/local/cargo/ && \
    echo '[source.crates-io]' >> /usr/local/cargo/config.toml && \
    echo 'replace-with = "rsproxy-sparse"' >> /usr/local/cargo/config.toml && \
    echo '[source.rsproxy-sparse]' >> /usr/local/cargo/config.toml && \
    echo 'registry = "sparse+https://rsproxy.cn/index/"' >> /usr/local/cargo/config.toml

# 依赖文件 + 锁文件（锁定依赖版本）
COPY Cargo.toml Cargo.lock ./

# SQLx 离线元数据（query!/query_as! 宏编译期校验不依赖数据库）
COPY .sqlx ./.sqlx

# 源代码与迁移脚本（迁移由 db-init 在数据库侧执行，这里仅随镜像保留）
COPY migrations ./migrations
COPY src ./src

# 关键：离线模式，禁止构建期连接数据库
ENV SQLX_OFFLINE=true

RUN cargo build --release --locked

# ── 运行时镜像 ──
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/file-service /usr/local/bin/file-service

EXPOSE 8007

HEALTHCHECK --interval=15s --timeout=5s --retries=15 --start-period=30s \
  CMD curl -fsS http://localhost:8007/health >/dev/null || exit 1

CMD ["file-service"]