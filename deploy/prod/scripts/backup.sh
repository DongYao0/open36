#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Open436 生产数据备份
#
#  备份对象（每个均为空 → 跳过但报告，不冒充成功）：
#    - PostgreSQL open436 + ai_db
#    - MySQL hoj（仅 --profile hoj）
#    - MinIO 对象桶
#
#  产物：deploy/prod/backups/<timestamp>/ 下 gzip SQL + 对象镜像
#
#  用法：bash deploy/prod/scripts/backup.sh
#
#  注意：本脚本必须以 docker 组成员身份运行；否则 docker exec / docker run 会失败。
#
#  严格约束：
#    1) 找不到目标容器 → 记录 SKIP 但 exit code 反映真实情况（不全为 0）
#    2) MinIO mc 镜像的 entrypoint 必须被显式覆盖为 /bin/sh，命令体内再调 mc
#    3) BACKUP_INTEGRITY_CHECK=1 时仅做 gzip 完整性校验（**不称为恢复演练**）
# ─────────────────────────────────────────────────────────────
set -euo pipefail
umask 077

PROD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${OPEN436_ENV_FILE:-$PROD_DIR/.env.production}"
[ -f "$ENV_FILE" ] || { echo "[backup][FATAL] missing $ENV_FILE" >&2; exit 66; }
set -a && . "$ENV_FILE" && set +a
: "${COMPOSE_PROJECT_NAME:?missing COMPOSE_PROJECT_NAME}"
: "${POSTGRES_USER:?missing POSTGRES_USER}"
: "${POSTGRES_DB:?missing POSTGRES_DB}"
: "${MINIO_ROOT_USER:?missing MINIO_ROOT_USER}"
: "${MINIO_ROOT_PASSWORD:?missing MINIO_ROOT_PASSWORD}"
: "${MINIO_BUCKET:?missing MINIO_BUCKET}"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$PROD_DIR/backups/$STAMP"
mkdir -p "$OUT"

# Compose v2 项目命名
PROJECT="$COMPOSE_PROJECT_NAME"
NET_INTERNAL="${PROJECT}_internal"

# 用 docker compose ps -q 精确查找容器（项目下每个 service 一个）
# fall back to docker ps -qf name=<project>-<service>-
echo "[backup] target: $OUT"
echo "[backup] project: $PROJECT  net: $NET_INTERNAL"

# 提取容器 ID：先尝试 compose ps，再退到 ps -q name 匹配
get_ct() {
    local svc="$1"
    # 项目内 service 名 → 容器 id
    local id
    id="$(docker compose --env-file "$ENV_FILE" -f "$PROD_DIR/compose.yml" -p "$PROJECT" ps -q "$svc" 2>/dev/null | head -1)"
    if [ -n "$id" ]; then
        echo "$id"
        return
    fi
    # 回退到 docker ps -q name 模式
    docker ps -qf "name=^/${PROJECT}-${svc}(-1)?$" 2>/dev/null | head -1
}

postgres_ct="$(get_ct postgres)"
hoj_mysql_ct="$(get_ct hoj-mysql)"
minio_ct="$(get_ct minio)"

echo "[backup] found containers: postgres=${postgres_ct:-NONE} hoj-mysql=${hoj_mysql_ct:-NONE} minio=${minio_ct:-NONE}"

BACKUP_OK=0
BACKUP_FAIL=0

# 应用层业务库名（来自 .env.production）
APP_DB="$POSTGRES_DB"

# ── PostgreSQL ──
if [ -n "$postgres_ct" ]; then
  echo "[backup] postgres -> ${APP_DB}.sql.gz"
  if docker exec "$postgres_ct" \
      pg_dump -U "$POSTGRES_USER" -d "${APP_DB}" \
      | gzip > "$OUT/${APP_DB}.sql.gz"; then
    sz=$(stat -c%s "$OUT/${APP_DB}.sql.gz" 2>/dev/null || stat -f%z "$OUT/${APP_DB}.sql.gz")
    if [ "${sz:-0}" -lt 100 ]; then
      echo "[backup][FAIL] ${APP_DB}.sql.gz 仅 $sz 字节，疑似空库或导出失败"
      BACKUP_FAIL=$((BACKUP_FAIL + 1))
    else
      echo "[backup] OK: ${APP_DB}.sql.gz ($sz bytes)"
      BACKUP_OK=$((BACKUP_OK + 1))
    fi
  else
    echo "[backup][FAIL] pg_dump ${APP_DB} 失败"
    BACKUP_FAIL=$((BACKUP_FAIL + 1))
  fi

  echo "[backup] postgres -> ai_db.sql.gz"
  if docker exec "$postgres_ct" \
      pg_dump -U "$POSTGRES_USER" -d ai_db \
      | gzip > "$OUT/ai_db.sql.gz"; then
    sz=$(stat -c%s "$OUT/ai_db.sql.gz" 2>/dev/null || stat -f%z "$OUT/ai_db.sql.gz")
    if [ "${sz:-0}" -lt 100 ]; then
      echo "[backup][WARN] ai_db.sql.gz 仅 $sz 字节（可能库空）"
    else
      echo "[backup] OK: ai_db.sql.gz ($sz bytes)"
      BACKUP_OK=$((BACKUP_OK + 1))
    fi
  else
    echo "[backup][WARN] pg_dump ai_db 失败（库可能不存在）"
  fi
else
  echo "[backup][SKIP] postgres 容器未运行"
fi

# ── MySQL（HOJ）──
if [ -n "$hoj_mysql_ct" ]; then
  echo "[backup] mysql (hoj) -> hoj.sql.gz"
  if docker exec "$hoj_mysql_ct" \
      sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" hoj' \
      | gzip > "$OUT/hoj.sql.gz"; then
    sz=$(stat -c%s "$OUT/hoj.sql.gz" 2>/dev/null || stat -f%z "$OUT/hoj.sql.gz")
    if [ "${sz:-0}" -lt 100 ]; then
      echo "[backup][WARN] hoj.sql.gz 仅 $sz 字节（可能库空）"
    else
      echo "[backup] OK: hoj.sql.gz ($sz bytes)"
      BACKUP_OK=$((BACKUP_OK + 1))
    fi
  else
    echo "[backup][FAIL] mysqldump hoj 失败"
    BACKUP_FAIL=$((BACKUP_FAIL + 1))
  fi
else
  echo "[backup][SKIP] hoj-mysql 容器未运行（profile hoj 未启用）"
fi

# ── MinIO 对象 ──
# mc 镜像 entrypoint=/usr/bin/mc，必须覆盖为 /bin/sh 才能跑多命令
if [ -n "$minio_ct" ]; then
  BUCKET="$MINIO_BUCKET"
  echo "[backup] minio objects -> minio/$BUCKET/"
  MINIO_OUT="$OUT/minio/$BUCKET"
  mkdir -p "$MINIO_OUT"
  if MSYS_NO_PATHCONV=1 docker run --rm \
      --network "$NET_INTERNAL" \
      --entrypoint /bin/sh \
      -v "$OUT:/backup" \
      -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD \
      minio/mc:RELEASE.2025-08-13T08-35-41Z \
      -c "
        set -eu
        mc alias set local http://minio:9000 \"\${MINIO_ROOT_USER}\" \"\${MINIO_ROOT_PASSWORD}\"
        if mc stat local/${BUCKET} >/dev/null 2>&1; then
          mc mirror --overwrite local/${BUCKET} /backup/minio/${BUCKET}/
          echo 'minio mirror OK'
        else
          echo 'minio bucket ${BUCKET} not found, skipping mirror' >&2
          exit 0
        fi
      " > "$OUT/minio-mirror.log" 2>&1; then
    n=$(find "$MINIO_OUT" -type f 2>/dev/null | wc -l)
    echo "[backup] OK: minio/${BUCKET}/ 共 $n 个对象"
    BACKUP_OK=$((BACKUP_OK + 1))
  else
    echo "[backup][FAIL] minio mirror 失败，详见 $OUT/minio-mirror.log"
    BACKUP_FAIL=$((BACKUP_FAIL + 1))
  fi
else
  echo "[backup][SKIP] minio 容器未运行"
fi

# ── 摘要 ──
echo ""
echo "[backup] 备份产物："
ls -la "$OUT" 2>/dev/null || true
echo ""
echo "[backup] OK=$BACKUP_OK FAIL=$BACKUP_FAIL OUT=$OUT"

# ── gzip 完整性校验（**仅完整性**，不是恢复演练）──
#   完整恢复请用 deploy/prod/scripts/restore.sh
if [ "${BACKUP_INTEGRITY_CHECK:-0}" = "1" ]; then
  echo ""
  echo "[backup][INTEGRITY] 校验 gzip 完整性（仅验证 gzip 是否可解压）："
  for f in "$OUT"/*.sql.gz; do
    [ -f "$f" ] || continue
    if gunzip -t "$f" 2>/dev/null; then
      echo "  OK: $(basename "$f")"
    else
      echo "  FAIL: $(basename "$f")"
      BACKUP_FAIL=$((BACKUP_FAIL + 1))
    fi
  done
fi

# ── 退出码策略（必须在完整性校验之后判断）──
if [ "$BACKUP_FAIL" -gt 0 ]; then
  echo "[backup] PARTIAL FAILURE (exit 2)"
  exit 2
fi
if [ "$BACKUP_OK" -eq 0 ]; then
  echo "[backup] NOTHING TO BACKUP：所有目标容器均未运行 (exit 3)"
  exit 3
fi

echo "[backup] SUCCESS"
exit 0
