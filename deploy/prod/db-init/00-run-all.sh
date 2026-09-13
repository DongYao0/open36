#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Open436 生产数据库首次初始化（仅空卷首启触发）
#
#  白名单导入（生产）：
#    1) ai_db 数据库 + AI 表（001_init.sql）
#    2) FileService 表（migrations/*.sql）
#    3) Forum 表（严格白名单：仅 V1__create_sections_table.sql、
#                            V2__create_forum_tables.sql、
#                            V3__add_post_ai_generated.sql）
#    4) Auth / Enrollment 表：**不由本脚本导入**，由各自 Spring Boot Flyway
#       用独立 history table（auth_flyway_schema_history /
#       enrollment_flyway_schema_history）自管。
#
#  严禁导入 db-init/seed_new_students.sql：
#    该脚本内含硬编码测试账号 open436admin/Open436@2024，
#    生产环境必须通过 ADMIN_BOOTSTRAP_USER / ADMIN_BOOTSTRAP_PASSWORD_HASH
#    环境变量，由 Spring Boot 应用启动时的 ProductionAdminInitializer
#    （Open436-Auth/.../config/ProductionAdminInitializer.java）自动完成。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

DB_USER="${POSTGRES_USER:-open436}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

run_sql_file() {
  local db="$1" file="$2"
  echo "[db-init] $db <- $(basename "$file")"
  psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$db" -f "$file"
}

# 1) ai_db 数据库 + AI 表
if psql -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ai_db'" | grep -q 1; then
  echo "[db-init] ai_db already exists, skip create"
else
  createdb -U "$DB_USER" ai_db
  echo "[db-init] created ai_db"
fi
run_sql_file ai_db /docker-entrypoint-initdb.d/ai/001_init.sql

# 2) FileService 表（public schema；仅由 PostgreSQL 空卷初始化入口执行一次）
for f in /docker-entrypoint-initdb.d/file_migrations/*.sql; do
  run_sql_file "${POSTGRES_DB:-open436}" "$f"
done

# 3) Forum 表 —— 严格白名单；seed_new_students.sql 绝不执行
FORUM_WHITELIST=(
  "/docker-entrypoint-initdb.d/forum/V1__create_sections_table.sql"
  "/docker-entrypoint-initdb.d/forum/V2__create_forum_tables.sql"
  "/docker-entrypoint-initdb.d/forum/V3__add_post_ai_generated.sql"
)
for f in "${FORUM_WHITELIST[@]}"; do
  if [ ! -f "$f" ]; then
    echo "[db-init][FATAL] 白名单文件缺失: $f"
    exit 1
  fi
  run_sql_file "${POSTGRES_DB:-open436}" "$f"
done

echo "[db-init] done"
