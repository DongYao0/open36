#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  重新生成 FileService 的 SQLx 离线元数据（.sqlx/）+ 兼容的 Cargo.lock
#
#  用途：当 FileService 的 SQL（query!/query_as!）、迁移文件或依赖变更后，
#  需要刷新已提交的离线元数据，保证生产 Docker 构建（SQLX_OFFLINE=true）
#  仍能在无数据库的干净环境编译通过。
#
#  前置：本机已安装 docker；可联网拉取 postgres 与 rust 镜像。
#
#  流程：
#    1) 临时 Postgres，应用 migrations；
#    2) 在 rust:1.85.0-bookworm 容器内：
#       a) cargo install sqlx-cli 0.7.4（与 sqlx 0.7 crate 严格匹配）
#       b) cargo update 降级已知需 1.88 的传递依赖到 1.85 兼容版本
#       c) cargo sqlx prepare 生成 .sqlx/
#    3) 仅清理本次创建的临时容器与临时目录。
#
#  注意：不要在生产机运行；运行后请 git add .sqlx/ Cargo.lock 提交。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
FS_DIR="$ROOT/Open436-FileService"
RUST_IMAGE="rust:1.85.0-bookworm"
PG_IMAGE="postgres:14-alpine"
CTN="open436-sqlx-prep-$$"
WORK_TMP="$(mktemp -d -t open436-sqlx.XXXXXXXX)"
PG_PASSWORD="$(openssl rand -hex 24)"

cleanup() {
  docker rm -f "$CTN-db" >/dev/null 2>&1 || true
  case "$WORK_TMP" in
    /tmp/open436-sqlx.*) rm -rf -- "$WORK_TMP" ;;
    *) echo "[sqlx][WARN] refuse to remove unexpected temp path: $WORK_TMP" >&2 ;;
  esac
}
trap cleanup EXIT

echo "[sqlx] using FileService dir: $FS_DIR"

# 1) 临时 Postgres + 应用 migrations
echo "[sqlx] starting temp postgres..."
docker run -d --name "$CTN-db" \
  -e POSTGRES_USER=open436 -e POSTGRES_PASSWORD="$PG_PASSWORD" -e POSTGRES_DB=open436 \
  "$PG_IMAGE" >/dev/null

for i in $(seq 1 60); do
  docker exec "$CTN-db" pg_isready -U open436 >/dev/null 2>&1 && break
  sleep 1
done

for f in "$FS_DIR"/migrations/*.sql; do
  echo "[sqlx] apply $(basename "$f")"
  docker exec -i "$CTN-db" psql -U open436 -d open436 -v ON_ERROR_STOP=1 < "$f" >/dev/null
done

# 2) rust 容器内：装 sqlx-cli、生成 .sqlx
echo "[sqlx] building (generates .sqlx + compatible Cargo.lock)..."
MSYS_NO_PATHCONV=1 docker run --rm --network "container:$CTN-db" \
  -v "$FS_DIR:/app" \
  -v "$WORK_TMP/target:/app/target" \
  -v "$WORK_TMP/cargo:/usr/local/cargo" \
  -w /app \
  -e DATABASE_URL="postgresql://open436:$PG_PASSWORD@localhost:5432/open436" \
  "$RUST_IMAGE" bash -c '
    mkdir -p /usr/local/cargo &&
    printf "[source.crates-io]\nreplace-with = \"rsproxy-sparse\"\n[source.rsproxy-sparse]\nregistry = \"sparse+https://rsproxy.cn/index/\"\n" > /usr/local/cargo/config.toml &&
    echo "[sqlx] installing sqlx-cli 0.7.4..." &&
    cargo install sqlx-cli --version 0.7.4 --locked --no-default-features --features rustls,postgres 2>&1 | tail -3 &&
    echo "[sqlx] downgrading deps that require rustc 1.88 to 1.85-compatible versions..." &&
    cargo update -p time --precise 0.3.36 2>&1 | tail -2 &&
    cargo update -p idna_adapter --precise 1.1.0 2>&1 | tail -2 &&
    cargo update -p multiversion --precise 0.7.3 2>&1 | tail -2 &&
    cargo update -p tracing-actix-web --precise 0.7.18 2>&1 | tail -2 &&
    cargo update 2>&1 | tail -2 &&
    echo "[sqlx] running cargo sqlx prepare..." &&
    /usr/local/cargo/bin/sqlx prepare --workspace 2>&1 | tail -10
  '

echo ""
echo "[sqlx] done."
echo "  .sqlx files: $(ls "$FS_DIR/.sqlx"/*.json 2>/dev/null | wc -l)"
echo "  Cargo.lock size: $(wc -c < "$FS_DIR/Cargo.lock" 2>/dev/null || echo 0) bytes"
echo "  请 git add $FS_DIR/.sqlx $FS_DIR/Cargo.lock 后再 build。"
