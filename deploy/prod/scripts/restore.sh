#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Open436 生产数据恢复（基于 backup.sh 产物）
#
#  用法：
#    bash deploy/prod/scripts/restore.sh <BACKUP_DIR>
#
#  <BACKUP_DIR> 形如 deploy/prod/backups/20260911-144700/
#
#  PostgreSQL 恢复前会重建 public schema，再导入结构与数据。
#  恢复前应停止所有应用容器，避免恢复期间继续写库。
#
#  PostgreSQL：psql 注入 gzip SQL
#  MySQL：     zcat 后 mysql 命令行导入
#  MinIO：     mc mirror 反向同步回 MinIO 桶
#
#  重要：恢复前会自动确认目标容器名与 backup 时间戳匹配。
#  恢复过程不可逆——执行前会提示二次确认（除非 RESTORE_FORCE=1）。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

PROD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${OPEN436_ENV_FILE:-$PROD_DIR/.env.production}"
[ -f "$ENV_FILE" ] || { echo "[restore][FATAL] missing $ENV_FILE" >&2; exit 66; }
set -a && . "$ENV_FILE" && set +a
: "${COMPOSE_PROJECT_NAME:?missing COMPOSE_PROJECT_NAME}"
: "${POSTGRES_USER:?missing POSTGRES_USER}"
: "${POSTGRES_DB:?missing POSTGRES_DB}"
: "${MINIO_ROOT_USER:?missing MINIO_ROOT_USER}"
: "${MINIO_ROOT_PASSWORD:?missing MINIO_ROOT_PASSWORD}"
: "${MINIO_BUCKET:?missing MINIO_BUCKET}"

BACKUP_DIR="${1:-}"
if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
  echo "Usage: $0 <BACKUP_DIR>"
  echo "  <BACKUP_DIR> e.g. deploy/prod/backups/20260911-144700"
  exit 64
fi

PROJECT="$COMPOSE_PROJECT_NAME"
NET_INTERNAL="${PROJECT}_internal"

# 在任何破坏性操作前先验证所有 SQL 压缩包。
for archive in "$BACKUP_DIR"/*.sql.gz; do
  [ -f "$archive" ] || continue
  gunzip -t "$archive" || {
    echo "[restore][FATAL] 损坏的备份文件: $archive"
    exit 65
  }
done

get_ct() {
    docker compose --env-file "$ENV_FILE" -f "$PROD_DIR/compose.yml" -p "$PROJECT" ps -q "$1" 2>/dev/null | head -1
}
postgres_ct="$(get_ct postgres)"
hoj_mysql_ct="$(get_ct hoj-mysql)"
minio_ct="$(get_ct minio)"

# ── 二次确认 ──
if [ "${RESTORE_FORCE:-0}" != "1" ]; then
  echo "[restore] !!! 警告：恢复操作不可逆 !!!"
  echo "  BACKUP_DIR = $BACKUP_DIR"
  echo "  POSTGRES_CT = ${postgres_ct:-NONE}"
  echo "  HOJ_MYSQL_CT = ${hoj_mysql_ct:-NONE}"
  echo "  MINIO_CT = ${minio_ct:-NONE}"
  echo ""
  read -r -p "确认继续? [y/N] " ans
  case "$ans" in
    y|Y|yes|YES) ;;
    *) echo "[restore] abort"; exit 1 ;;
  esac
fi

echo "[restore] start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
RESTORE_FAIL=0

# 应用层业务库名（来自 .env.production）
APP_DB="$POSTGRES_DB"

# ── PostgreSQL ──
if [ -n "$postgres_ct" ]; then
  restore_postgres_archive() {
    local src="$1"
    local db_name="$2"
    echo "[restore] postgres ${db_name} from $src"
    if ! docker exec "$postgres_ct" psql \
      -U "$POSTGRES_USER" -d "$db_name" -v ON_ERROR_STOP=1 \
      -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'; then
      echo "[restore][FAIL] reset postgres schema: $db_name"
      RESTORE_FAIL=1
      return
    fi
    if ! gunzip -c "$src" | docker exec -i "$postgres_ct" \
      psql -U "$POSTGRES_USER" -d "$db_name" -v ON_ERROR_STOP=1; then
      echo "[restore][FAIL] import postgres: $db_name"
      RESTORE_FAIL=1
    fi
  }

  app_src="$BACKUP_DIR/${APP_DB}.sql.gz"
  if [ ! -f "$app_src" ] && [ "$APP_DB" != "open436" ] && [ -f "$BACKUP_DIR/open436.sql.gz" ]; then
    app_src="$BACKUP_DIR/open436.sql.gz"
  fi
  [ ! -f "$app_src" ] || restore_postgres_archive "$app_src" "$APP_DB"

  ai_src="$BACKUP_DIR/ai_db.sql.gz"
  [ ! -f "$ai_src" ] || restore_postgres_archive "$ai_src" "ai_db"
elif [ -f "$BACKUP_DIR/${APP_DB}.sql.gz" ] || [ -f "$BACKUP_DIR/open436.sql.gz" ] || [ -f "$BACKUP_DIR/ai_db.sql.gz" ]; then
  echo "[restore][FAIL] PostgreSQL 备份存在，但 postgres 容器未运行"
  RESTORE_FAIL=1
fi

# ── MySQL ──
if [ -n "$hoj_mysql_ct" ]; then
  src="$BACKUP_DIR/hoj.sql.gz"
  if [ -f "$src" ]; then
    echo "[restore] mysql hoj from $src"
    gunzip -c "$src" | docker exec -i "$hoj_mysql_ct" \
      sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" hoj'
  fi
elif [ -f "$BACKUP_DIR/hoj.sql.gz" ]; then
  echo "[restore][FAIL] HOJ 备份存在，但 hoj-mysql 容器未运行"
  RESTORE_FAIL=1
fi

# ── MinIO ──
if [ -n "$minio_ct" ]; then
  BUCKET="$MINIO_BUCKET"
  src="$BACKUP_DIR/minio/$BUCKET"
  if [ -d "$src" ]; then
    echo "[restore] minio ${BUCKET} from $src"
    MSYS_NO_PATHCONV=1 docker run --rm \
      --network "$NET_INTERNAL" \
      --entrypoint /bin/sh \
      -v "$src:/src:ro" \
      -v "$BACKUP_DIR:/backup" \
      -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD \
      minio/mc:RELEASE.2025-08-13T08-35-41Z \
      -c "
        set -eu
        mc alias set local http://minio:9000 \"\${MINIO_ROOT_USER}\" \"\${MINIO_ROOT_PASSWORD}\"
        if ! mc stat local/${BUCKET} >/dev/null 2>&1; then
          mc mb local/${BUCKET}
        fi
        mc mirror --overwrite /src/ local/${BUCKET}/
        echo 'minio restore OK'
      "
  fi
elif [ -d "$BACKUP_DIR/minio" ]; then
  echo "[restore][FAIL] MinIO 备份存在，但 minio 容器未运行"
  RESTORE_FAIL=1
fi

if [ "$RESTORE_FAIL" -ne 0 ]; then
  echo "[restore] FAILED"
  exit 2
fi
echo "[restore] done: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[restore] 验证：在前端登录检查 Auth/Forum/FileService；HOJ 提交一次判题；MinIO 拉一张图。"
