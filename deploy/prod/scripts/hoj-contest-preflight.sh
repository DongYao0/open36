#!/usr/bin/env bash
# Open436 HOJ 赛前只读体检。仅检查 open436-prod-*，不访问其他 HOJ 实例。
set -uo pipefail

PREFIX="open436-prod"
TIMEOUT_SECONDS="${PREFLIGHT_TIMEOUT_SECONDS:-15}"
MAX_JUDGE_RESTARTS="${MAX_JUDGE_RESTARTS:-0}"
FAIL=0
WARN=0
PROBLEM_IDS=()
CONTEST_ID=""
CONTAINERS=(
  "${PREFIX}-redis" "${PREFIX}-hoj-mysql" "${PREFIX}-hoj-nacos"
  "${PREFIX}-go-judge" "${PREFIX}-hoj-backend" "${PREFIX}-hoj-judge"
  "${PREFIX}-hoj-vue" "${PREFIX}-public-web"
)

usage() {
  echo "用法: bash $0 [--contest-id 1] [--problem-ids 1001,1002] [problem_id ...]"
  echo "环境变量: PREFLIGHT_TIMEOUT_SECONDS=15 MAX_JUDGE_RESTARTS=0"
}
fail() { echo "[FAIL] $*"; FAIL=$((FAIL + 1)); }
warn() { echo "[WARN] $*"; WARN=$((WARN + 1)); }
ok() { echo "[ OK ] $*"; }
run() { timeout "${TIMEOUT_SECONDS}s" "$@"; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --contest-id)
      [ "$#" -ge 2 ] || { echo "[FATAL] --contest-id 缺少值" >&2; exit 2; }
      CONTEST_ID="$2"
      shift 2
      ;;
    --problem-ids)
      [ "$#" -ge 2 ] || { echo "[FATAL] --problem-ids 缺少值" >&2; exit 2; }
      IFS=',' read -r -a parsed_ids <<< "$2"
      PROBLEM_IDS+=("${parsed_ids[@]}")
      shift 2
      ;;
    --problem-ids=*)
      IFS=',' read -r -a parsed_ids <<< "${1#*=}"
      PROBLEM_IDS+=("${parsed_ids[@]}")
      shift
      ;;
    --*) echo "[FATAL] 未知参数: $1" >&2; usage >&2; exit 2 ;;
    *) PROBLEM_IDS+=("$1"); shift ;;
  esac
done

command -v docker >/dev/null 2>&1 || { echo "[FATAL] 未找到 docker" >&2; exit 2; }
command -v timeout >/dev/null 2>&1 || { echo "[FATAL] 未找到 timeout" >&2; exit 2; }
[[ "$TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || { echo "[FATAL] 超时必须为正整数" >&2; exit 2; }
[[ "$MAX_JUDGE_RESTARTS" =~ ^[0-9]+$ ]] || { echo "[FATAL] 重启阈值必须为非负整数" >&2; exit 2; }
[[ -z "$CONTEST_ID" || "$CONTEST_ID" =~ ^[1-9][0-9]*$ ]] || { echo "[FATAL] 非法 contest ID: $CONTEST_ID" >&2; exit 2; }

if [ -n "$CONTEST_ID" ]; then
  contest_ids="$(run docker exec "${PREFIX}-hoj-mysql" sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -Nse "SELECT pid FROM hoj.contest_problem WHERE cid=$1 ORDER BY display_id"' sh "$CONTEST_ID" 2>/dev/null)" || contest_ids=""
  [ -n "$contest_ids" ] || { echo "[FATAL] 比赛 $CONTEST_ID 不存在题目或数据库查询失败" >&2; exit 2; }
  while IFS= read -r pid; do [ -n "$pid" ] && PROBLEM_IDS+=("$pid"); done <<< "$contest_ids"
  echo "比赛 $CONTEST_ID 题目: ${PROBLEM_IDS[*]}"
fi
for pid in "${PROBLEM_IDS[@]}"; do
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] || { echo "[FATAL] 非法 problem ID: $pid" >&2; exit 2; }
done

echo "== Open436 HOJ 赛前体检（只读） =="
echo "目标前缀: ${PREFIX}-* | 单命令超时: ${TIMEOUT_SECONDS}s"
echo
echo "-- 容器运行与健康状态 --"
for ct in "${CONTAINERS[@]}"; do
  state="$(run docker inspect -f '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$ct" 2>/dev/null)" || state=""
  if [ -z "$state" ]; then
    fail "$ct 不存在或无法读取"
  elif [ "$state" = "running|healthy" ]; then
    ok "$ct: running / healthy"
  elif [ "$state" = "running|none" ]; then
    warn "$ct: running / 无 healthcheck"
  else
    fail "$ct: ${state/|/ / }"
  fi
done

echo
echo "-- 容器瞬时资源快照 --"
if ! run docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.PIDs}}' "${CONTAINERS[@]}"; then
  fail "docker stats 获取失败或超时"
fi

echo
echo "-- Judge 重启与 OOM --"
JUDGE="${PREFIX}-hoj-judge"
judge_state="$(run docker inspect -f '{{.RestartCount}}|{{.State.OOMKilled}}|{{.State.ExitCode}}' "$JUDGE" 2>/dev/null)" || judge_state=""
if [[ "$judge_state" =~ ^([0-9]+)\|(true|false)\|(-?[0-9]+)$ ]]; then
  restarts="${BASH_REMATCH[1]}"; oom="${BASH_REMATCH[2]}"; exit_code="${BASH_REMATCH[3]}"
  [ "$oom" = false ] && ok "Judge 未记录 OOM" || fail "Judge 记录到 OOMKilled=true"
  [ "$restarts" -le "$MAX_JUDGE_RESTARTS" ] && ok "Judge 重启次数 $restarts（阈值 $MAX_JUDGE_RESTARTS）" || fail "Judge 重启次数 $restarts 超过阈值 $MAX_JUDGE_RESTARTS"
  [ "$exit_code" -eq 0 ] || warn "Judge 最近退出码为 $exit_code"
else
  fail "Judge 状态读取失败"
fi

echo
echo "-- 主机容量 --"
disk_used="$(df -P /var/lib/docker 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
[ -n "$disk_used" ] || disk_used="$(df -P / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
if [[ "$disk_used" =~ ^[0-9]+$ ]]; then
  [ "$disk_used" -lt 85 ] && ok "Docker 所在磁盘使用率 ${disk_used}%" || fail "Docker 所在磁盘使用率 ${disk_used}%（需低于 85%）"
else
  warn "无法读取磁盘使用率"
fi
mem_kb="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo 2>/dev/null)"
if [[ "$mem_kb" =~ ^[0-9]+$ ]]; then
  mem_gb=$((mem_kb / 1024 / 1024))
  [ "$mem_kb" -ge 8388608 ] && ok "主机可用内存约 ${mem_gb} GiB" || fail "主机可用内存约 ${mem_gb} GiB（需至少 8 GiB）"
else
  warn "无法读取主机可用内存"
fi

echo
echo "-- 比赛题测试数据 --"
if [ "${#PROBLEM_IDS[@]}" -eq 0 ]; then
  warn "未传 problem ID，跳过测试数据检查"
else
  for pid in "${PROBLEM_IDS[@]}"; do
    db_count="$(run docker exec "${PREFIX}-hoj-mysql" sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -Nse "SELECT COUNT(*) FROM hoj.problem_case WHERE pid=$1 AND status=0"' sh "$pid" 2>/dev/null)" || db_count=""
    if [[ "$db_count" =~ ^[1-9][0-9]*$ ]]; then ok "题目 $pid: 数据库有 $db_count 个可用测试点"; else fail "题目 $pid: 数据库无可用测试点或查询失败"; fi
    detail="$(run docker exec "${PREFIX}-hoj-judge" sh -c '
      d="/judge/test_case/problem_$1"; [ -d "$d" ] || { echo "目录不存在"; exit 1; }
      [ -s "$d/info" ] || { echo "info 缺失或为空"; exit 1; }
      inputs=0; outputs=0
      for f in "$d"/*.in; do [ -e "$f" ] || continue; inputs=$((inputs+1)); b=${f%.in}; [ -f "$b.out" ] || [ -f "$b.ans" ] || { echo "$(basename "$f") 缺少对应输出"; exit 1; }; done
      for f in "$d"/*.out "$d"/*.ans; do [ -e "$f" ] && outputs=$((outputs+1)); done
      [ "$inputs" -gt 0 ] || { echo "无 .in 文件"; exit 1; }
      [ "$outputs" -ge "$inputs" ] || { echo "输出文件少于输入文件"; exit 1; }
      echo "$inputs 对输入输出，info 完整"
    ' sh "$pid" 2>&1)"
    [ "$?" -eq 0 ] && ok "题目 $pid: $detail" || fail "题目 $pid: $detail"
  done
fi

echo
echo "== 汇总: FAIL=$FAIL WARN=$WARN =="
[ "$FAIL" -eq 0 ] || exit 1
echo "赛前体检通过"
