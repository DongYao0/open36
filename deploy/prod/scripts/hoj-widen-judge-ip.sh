#!/usr/bin/env bash
# Open436 HOJ：把 hoj.judge.ip 从 varchar(20) 扩到 varchar(45)。
#
# 背景（2026-09-29 根因）：judge.ip 为 varchar(20)，而标准 IPv6 最长 45 字符
# （IPv4-mapped 完全展开形式）。代理头一旦传入 IPv6 或超长内容，提交落库即报
# `Data too long for column 'ip'`，导致提交记录写入失败。
#
# 本脚本幂等、只读校验 + 单列 ALTER，不触碰任何业务数据，不做破坏性迁移。
# 仅作用于 open436-prod-* 自己的容器。
set -uo pipefail

PREFIX="${PREFIX:-open436-prod}"
MYSQL_CT="${PREFIX}-hoj-mysql"
DB="${HOJ_DB_NAME:-hoj}"
TARGET_LEN=45
TIMEOUT_SECONDS="${HOJ_DB_MIGRATION_TIMEOUT_SECONDS:-60}"

command -v docker >/dev/null 2>&1 || { echo "[FATAL] 未找到 docker" >&2; exit 2; }
command -v timeout >/dev/null 2>&1 || { echo "[FATAL] 未找到 timeout" >&2; exit 2; }
[[ "$TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || { echo "[FATAL] 超时必须为正整数" >&2; exit 2; }
timeout "${TIMEOUT_SECONDS}s" docker inspect "$MYSQL_CT" >/dev/null 2>&1 \
  || { echo "[FATAL] 容器 $MYSQL_CT 不存在或检查超时" >&2; exit 2; }

myq() {
  # SQL 通过 stdin 传入，避免多层引号转义问题
  printf '%s\n' "$1" | timeout "${TIMEOUT_SECONDS}s" docker exec -i "$MYSQL_CT" \
    sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N '"$DB" 2>/dev/null
}

current="$(myq "SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='$DB' AND TABLE_NAME='judge' AND COLUMN_NAME='ip'")"
if [ -z "$current" ]; then
  echo "[FATAL] 找不到 $DB.judge.ip，脚本中止（不改动任何结构）" >&2
  exit 2
fi
echo "[INFO] 当前 judge.ip 类型: $current"

cur_len="$(printf '%s' "$current" | sed -n 's/^varchar(\([0-9]\+\))$/\1/p')"
if [ -z "$cur_len" ]; then
  echo "[WARN] judge.ip 不是 varchar(n)，请人工确认后处理，脚本不做改动" >&2
  exit 3
fi

if [ "$cur_len" -ge "$TARGET_LEN" ]; then
  echo "[ OK ] judge.ip 已是 varchar($cur_len) >= varchar($TARGET_LEN)，无需变更（幂等）"
  exit 0
fi

echo "[INFO] 将 judge.ip 从 varchar($cur_len) 扩到 varchar($TARGET_LEN)"
myq "ALTER TABLE judge MODIFY COLUMN ip varchar($TARGET_LEN) NULL COMMENT '客户端IP（IPv4/IPv6）'"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "[FAIL] ALTER 失败（rc=$rc）" >&2
  exit 1
fi

after="$(myq "SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='$DB' AND TABLE_NAME='judge' AND COLUMN_NAME='ip'")"
echo "[INFO] 变更后 judge.ip 类型: $after"
[ "$after" = "varchar($TARGET_LEN)" ] || { echo "[FAIL] 变更后类型不符合预期" >&2; exit 1; }

# 完整性校验：现有数据不受影响
cnt="$(myq "SELECT COUNT(*) FROM judge")"
maxlen="$(myq "SELECT COALESCE(MAX(CHAR_LENGTH(ip)),0) FROM judge")"
echo "[ OK ] judge 行数=$cnt，现有 ip 最长=$maxlen 字符（数据未受影响）"
echo "[ OK ] judge.ip 列宽已就绪（支持 IPv6，最长 45）"
