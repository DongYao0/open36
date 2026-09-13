#!/bin/bash
# ─────────────────────────────────────────────────────────────
# upgrade-forum-indexes.sh（阶段4.4）
#
# 对【已有数据卷】幂等应用论坛组合索引（新库首启走 00-run-all.sh
# 白名单，本脚本面向存量库——docker-entrypoint-initdb.d 不会重跑）。
#
# 用法（生产 Linux 上）：
#   cd deploy/prod && ../..//deploy/prod/scripts/upgrade-forum-indexes.sh
# 或：
#   bash deploy/prod/scripts/upgrade-forum-indexes.sh
#
# 行为：
#   1. 执行 db-init/V4__add_feed_composite_indexes.sql
#      （CREATE INDEX CONCURRENTLY IF NOT EXISTS，不锁写）；
#   2. 前后各做一次 EXPLAIN ANALYZE，结果存 /tmp/forum-index-explain-{before,after}.txt
#      作为阶段4.4验收证据。
#
# 注意：CONCURRENTLY 不能在事务块内运行，本脚本逐条执行，无 BEGIN。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

CONTAINER="${FORUM_PG_CONTAINER:-open436-prod-postgres}"
DB_USER="${POSTGRES_USER:-open436}"
DB_NAME="${POSTGRES_DB:-open436}"
SQL_FILE="$(cd "$(dirname "$0")/../../.." && pwd)/db-init/V4__add_feed_composite_indexes.sql"

if [ ! -f "$SQL_FILE" ]; then
  echo "[upgrade][FATAL] 找不到 $SQL_FILE" >&2
  exit 1
fi

echo "[upgrade] before: EXPLAIN ANALYZE 存 /tmp/forum-index-explain-before.txt"
docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<'SQL' > /tmp/forum-index-explain-before.txt
EXPLAIN ANALYZE SELECT * FROM posts WHERE status = 1 ORDER BY is_pinned DESC, created_at DESC LIMIT 20;
EXPLAIN ANALYZE SELECT * FROM posts WHERE section_id = 1 AND status = 1 ORDER BY is_pinned DESC, created_at DESC LIMIT 20;
EXPLAIN ANALYZE SELECT * FROM replies WHERE post_id = 1 AND is_deleted = false ORDER BY floor_number LIMIT 50;
SQL

echo "[upgrade] applying V4+V5 indexes (CONCURRENTLY, idempotent)..."
docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < "$SQL_FILE"
V5_FILE="$(cd "$(dirname "$0")/../../.." && pwd)/db-init/V5__add_search_trgm_indexes.sql"
docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < "$V5_FILE"

echo "[upgrade] after: EXPLAIN ANALYZE 存 /tmp/forum-index-explain-after.txt"
docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<'SQL' > /tmp/forum-index-explain-after.txt
EXPLAIN ANALYZE SELECT * FROM posts WHERE status = 1 ORDER BY is_pinned DESC, created_at DESC LIMIT 20;
EXPLAIN ANALYZE SELECT * FROM posts WHERE section_id = 1 AND status = 1 ORDER BY is_pinned DESC, created_at DESC LIMIT 20;
EXPLAIN ANALYZE SELECT * FROM replies WHERE post_id = 1 AND is_deleted = false ORDER BY floor_number LIMIT 50;
SQL

echo "[upgrade] 当前索引状态："
docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "SELECT indexname FROM pg_indexes WHERE tablename IN ('posts','replies') AND indexname LIKE 'idx_%' ORDER BY 1;"
echo "[upgrade] done（请对比 /tmp/forum-index-explain-{before,after}.txt 确认走索引）"
