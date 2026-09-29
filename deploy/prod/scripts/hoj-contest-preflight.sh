#!/usr/bin/env bash
# Open436 HOJ 赛前只读体检（扩展版）。
#
# 只检查 open436-prod-* 自己的容器与数据；不访问、不修改任何其他 HOJ 实例。
# 默认不改动比赛数据；唯一可选写入是 PREFLIGHT_E2E=1 时的一次真实试判提交。
#
# 退出码：
#   0 = PASS 可以开赛
#   1 = FAIL 禁止开赛（已列出具体服务/题号/文件）
#   2 = 用法或前置条件错误
set -uo pipefail

PREFIX="${PREFIX:-open436-prod}"
TIMEOUT_SECONDS="${PREFLIGHT_TIMEOUT_SECONDS:-15}"
MAX_JUDGE_RESTARTS="${MAX_JUDGE_RESTARTS:-0}"
MIN_TUNNEL_CONNECTIONS="${MIN_TUNNEL_CONNECTIONS:-2}"
DISK_MAX_PERCENT="${DISK_MAX_PERCENT:-85}"
INODE_MAX_PERCENT="${INODE_MAX_PERCENT:-85}"
MIN_FREE_MEM_MB="${MIN_FREE_MEM_MB:-8192}"
E2E_ENABLED="${PREFLIGHT_E2E:-0}"
E2E_USER="${HOJ_E2E_USER:-}"
E2E_PASS="${HOJ_E2E_PASS:-}"
E2E_PID="${HOJ_E2E_PID:-}"
E2E_LANG="${HOJ_E2E_LANG:-C++}"
E2E_TIMEOUT_SECONDS="${HOJ_E2E_TIMEOUT_SECONDS:-120}"
HOJ_DB="${HOJ_DB_NAME:-hoj}"

FAIL=0
WARN=0
PROBLEM_IDS=()
CONTEST_ID=""

MYSQL_CT="${PREFIX}-hoj-mysql"
JUDGE_CT="${PREFIX}-hoj-judge"
BACKEND_CT="${PREFIX}-hoj-backend"
REDIS_CT="${PREFIX}-redis"
NACOS_CT="${PREFIX}-hoj-nacos"
GOJUDGE_CT="${PREFIX}-go-judge"
PUBLIC_WEB_CT="${PREFIX}-public-web"
VUE_CT="${PREFIX}-hoj-vue"
TUNNEL_CT="${PREFIX}-cloudflared"

CONTAINERS=(
  "$REDIS_CT" "$MYSQL_CT" "$NACOS_CT" "$GOJUDGE_CT"
  "$BACKEND_CT" "$JUDGE_CT" "$VUE_CT" "$PUBLIC_WEB_CT" "$TUNNEL_CT"
)

usage() {
  echo "用法: bash $0 [--contest-id 1] [--problem-ids 1001,1002] [problem_id ...]"
  echo "环境变量:"
  echo "  PREFLIGHT_TIMEOUT_SECONDS=15   单条命令超时"
  echo "  MAX_JUDGE_RESTARTS=0           Judge 允许的历史重启基线"
  echo "  MIN_TUNNEL_CONNECTIONS=2       隧道最低活跃连接数"
  echo "  DISK_MAX_PERCENT=85 INODE_MAX_PERCENT=85 MIN_FREE_MEM_MB=8192"
  echo "  PREFLIGHT_E2E=1                开启端到端试判（需下面三项）"
  echo "  HOJ_E2E_USER= HOJ_E2E_PASS= HOJ_E2E_PID= [HOJ_E2E_LANG=C++]"
}
fail() { echo "[FAIL] $*"; FAIL=$((FAIL + 1)); }
warn() { echo "[WARN] $*"; WARN=$((WARN + 1)); }
ok()   { echo "[ OK ] $*"; }
run()  { timeout "${TIMEOUT_SECONDS}s" "$@"; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --contest-id)
      [ "$#" -ge 2 ] || { echo "[FATAL] --contest-id 缺少值" >&2; exit 2; }
      CONTEST_ID="$2"; shift 2 ;;
    --problem-ids)
      [ "$#" -ge 2 ] || { echo "[FATAL] --problem-ids 缺少值" >&2; exit 2; }
      IFS=',' read -r -a parsed_ids <<< "$2"; PROBLEM_IDS+=("${parsed_ids[@]}"); shift 2 ;;
    --problem-ids=*)
      IFS=',' read -r -a parsed_ids <<< "${1#*=}"; PROBLEM_IDS+=("${parsed_ids[@]}"); shift ;;
    --*) echo "[FATAL] 未知参数: $1" >&2; usage >&2; exit 2 ;;
    *) PROBLEM_IDS+=("$1"); shift ;;
  esac
done

command -v docker >/dev/null 2>&1 || { echo "[FATAL] 未找到 docker" >&2; exit 2; }
command -v timeout >/dev/null 2>&1 || { echo "[FATAL] 未找到 timeout" >&2; exit 2; }
[[ "$TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || { echo "[FATAL] 超时必须为正整数" >&2; exit 2; }
[[ "$MAX_JUDGE_RESTARTS" =~ ^[0-9]+$ ]] || { echo "[FATAL] 重启阈值必须为非负整数" >&2; exit 2; }
[[ -z "$CONTEST_ID" || "$CONTEST_ID" =~ ^[1-9][0-9]*$ ]] || { echo "[FATAL] 非法 contest ID: $CONTEST_ID" >&2; exit 2; }

# SQL 经 stdin 传入，避免多层引号问题
mysql_q() {
  printf '%s\n' "$1" | timeout "${TIMEOUT_SECONDS}s" docker exec -i "$MYSQL_CT" \
    sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" --default-character-set=utf8mb4 -N '"$HOJ_DB" 2>/dev/null
}

if [ -n "$CONTEST_ID" ]; then
  contest_ids="$(mysql_q "SELECT pid FROM contest_problem WHERE cid=$CONTEST_ID ORDER BY display_id")" || contest_ids=""
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

# ---------------------------------------------------------------- 1. 容器
echo "-- 1. 容器运行与健康 --"
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

# ---------------------------------------------------------------- 2. 依赖
echo
echo "-- 2. 依赖服务（MySQL / Redis / Nacos） --"
role_cnt="$(mysql_q 'SELECT COUNT(*) FROM role;')"
if [[ "$role_cnt" =~ ^[1-9][0-9]*$ ]]; then ok "MySQL 可查询（role 表 $role_cnt 行）"; else fail "MySQL 查询失败"; fi

redis_pass="$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$BACKEND_CT" 2>/dev/null | sed -n 's/^REDIS_PASSWORD=//p' | head -1)"
if [ -n "$redis_pass" ]; then
  rkey="open436:preflight:$$"
  if timeout "${TIMEOUT_SECONDS}s" docker exec -e REDISCLI_AUTH="$redis_pass" "$REDIS_CT" \
      sh -c 'redis-cli set "$1" ok >/dev/null && [ "$(redis-cli get "$1")" = ok ]' sh "$rkey"; then
    ok "Redis 可读写"
  else
    fail "Redis 读写失败"
  fi
  timeout "${TIMEOUT_SECONDS}s" docker exec -e REDISCLI_AUTH="$redis_pass" "$REDIS_CT" \
    redis-cli del "$rkey" >/dev/null 2>&1 || true
else
  warn "未取得 REDIS_PASSWORD，跳过 Redis 读写检查"
fi

nacos_h="$(timeout "${TIMEOUT_SECONDS}s" docker exec "$NACOS_CT" sh -c 'curl -fsS http://localhost:8848/nacos/actuator/health' 2>/dev/null)"
case "$nacos_h" in
  *'"status":"UP"'*) ok "Nacos 健康" ;;
  "") fail "Nacos 健康接口无响应" ;;
  *) fail "Nacos 健康异常: $nacos_h" ;;
esac

# ---------------------------------------------------------------- 3. 应用
echo
echo "-- 3. 应用健康（Backend / Judge / go-judge） --"
for pair in "$BACKEND_CT:http://localhost:6688/actuator/health:HOJ Backend" \
            "$JUDGE_CT:http://localhost:8088/actuator/health:HOJ Judge" \
            "$GOJUDGE_CT:http://localhost:5050/version:go-judge"; do
  ct="${pair%%:*}"; rest="${pair#*:}"; url="${rest%:*}"; label="${rest##*:}"
  body="$(timeout "${TIMEOUT_SECONDS}s" docker exec "$ct" sh -c "curl -fsS '$url'" 2>/dev/null)"
  if [ -n "$body" ]; then ok "$label 响应正常"; else fail "$label 健康接口无响应（$ct $url）"; fi
done

reg="$(mysql_q 'SELECT COUNT(*) FROM judge_server WHERE status=0;')"
if [[ "$reg" =~ ^[1-9][0-9]*$ ]]; then ok "Judge 已注册（可用节点 $reg 个）"; else fail "judge_server 无可用节点（status=0 数量=0）"; fi

# ---------------------------------------------------------------- 4. Judge 稳定性
echo
echo "-- 4. Judge 重启与 OOM --"
judge_state="$(run docker inspect -f '{{.RestartCount}}|{{.State.OOMKilled}}|{{.State.ExitCode}}' "$JUDGE_CT" 2>/dev/null)" || judge_state=""
if [[ "$judge_state" =~ ^([0-9]+)\|(true|false)\|(-?[0-9]+)$ ]]; then
  restarts="${BASH_REMATCH[1]}"; oom="${BASH_REMATCH[2]}"; exit_code="${BASH_REMATCH[3]}"
  [ "$oom" = false ] && ok "Judge 未记录 OOM" || fail "Judge 记录到 OOMKilled=true"
  [ "$restarts" -le "$MAX_JUDGE_RESTARTS" ] && ok "Judge 重启次数 $restarts（阈值 $MAX_JUDGE_RESTARTS）" \
    || fail "Judge 重启次数 $restarts 超过阈值 $MAX_JUDGE_RESTARTS"
  [ "$exit_code" -eq 0 ] || warn "Judge 最近退出码为 $exit_code"
else
  fail "Judge 状态读取失败"
fi

# ---------------------------------------------------------------- 5. 主机容量
echo
echo "-- 5. 主机容量（磁盘 / inode / 内存 / Swap） --"
disk_used="$(df -P /var/lib/docker 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
[ -n "$disk_used" ] || disk_used="$(df -P / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
if [[ "$disk_used" =~ ^[0-9]+$ ]]; then
  [ "$disk_used" -lt "$DISK_MAX_PERCENT" ] && ok "Docker 磁盘使用率 ${disk_used}%" \
    || fail "Docker 磁盘使用率 ${disk_used}%（需低于 ${DISK_MAX_PERCENT}%）"
else
  warn "无法读取磁盘使用率"
fi

inode_used="$(df -Pi /var/lib/docker 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
[ -n "$inode_used" ] || inode_used="$(df -Pi / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
if [[ "$inode_used" =~ ^[0-9]+$ ]]; then
  [ "$inode_used" -lt "$INODE_MAX_PERCENT" ] && ok "inode 使用率 ${inode_used}%" \
    || fail "inode 使用率 ${inode_used}%（需低于 ${INODE_MAX_PERCENT}%）"
else
  warn "无法读取 inode 使用率"
fi

mem_kb="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo 2>/dev/null)"
if [[ "$mem_kb" =~ ^[0-9]+$ ]]; then
  mem_mb=$((mem_kb / 1024))
  [ "$mem_mb" -ge "$MIN_FREE_MEM_MB" ] && ok "可用内存约 ${mem_mb} MiB" \
    || fail "可用内存约 ${mem_mb} MiB（需至少 ${MIN_FREE_MEM_MB} MiB）"
else
  warn "无法读取主机可用内存"
fi

swap_total="$(awk '/SwapTotal:/ {print $2}' /proc/meminfo 2>/dev/null)"
swap_free="$(awk '/SwapFree:/ {print $2}' /proc/meminfo 2>/dev/null)"
if [[ "$swap_total" =~ ^[0-9]+$ && "$swap_free" =~ ^[0-9]+$ ]]; then
  if [ "$swap_total" -eq 0 ]; then
    warn "主机未启用 Swap"
  else
    swap_used_pct=$(( (swap_total - swap_free) * 100 / swap_total ))
    [ "$swap_used_pct" -lt 50 ] && ok "Swap 使用率 ${swap_used_pct}%" \
      || warn "Swap 使用率 ${swap_used_pct}%（偏高，可能已发生换页）"
  fi
fi

# ---------------------------------------------------------------- 6. 隧道
echo
echo "-- 6. Cloudflare Tunnel 活跃连接 --"
tunnel_ip="$(run docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$TUNNEL_CT" 2>/dev/null)"
if [ -n "$tunnel_ip" ]; then
  ha="$(curl -fsS --max-time "$TIMEOUT_SECONDS" "http://${tunnel_ip}:20241/metrics" 2>/dev/null \
        | awk '/^cloudflared_tunnel_ha_connections/ {print $2; exit}')"
  if [[ "$ha" =~ ^[0-9]+$ ]]; then
    [ "$ha" -ge "$MIN_TUNNEL_CONNECTIONS" ] && ok "隧道活跃连接 $ha 条" \
      || fail "隧道活跃连接仅 $ha 条（需 ≥ ${MIN_TUNNEL_CONNECTIONS}）"
  else
    warn "无法读取隧道连接数（metrics 不可用）"
  fi
else
  fail "无法解析 $TUNNEL_CT 的容器地址"
fi

# ---------------------------------------------------------------- 7. 对外入口
echo
echo "-- 7. 对外入口 HTTP 探测（容器内，避开公网抖动） --"
probe_route() {
  local label="$1" ct="$2" path="$3" method="${4:-GET}"
  local code
  code="$(timeout "${TIMEOUT_SECONDS}s" docker exec "$ct" sh -c \
    "curl -s -o /dev/null -w '%{http_code}' -X $method --max-time $((TIMEOUT_SECONDS - 2)) 'http://localhost$path'" 2>/dev/null)"
  if [[ "$code" =~ ^[0-9]+$ ]] && [ "$code" -ge 200 ] && [ "$code" -lt 500 ]; then
    ok "$label ${method} ${path} → ${code}"
  elif [ "$code" = "000" ] || [ -z "$code" ]; then
    fail "$label ${method} ${path} 无响应"
  else
    fail "$label ${method} ${path} → ${code}"
  fi
}
probe_route "首页"       "$PUBLIC_WEB_CT" "/"
probe_route "客户端页面" "$PUBLIC_WEB_CT" "/app/"
probe_route "登录页"     "$PUBLIC_WEB_CT" "/app/login"
probe_route "题目列表"   "$PUBLIC_WEB_CT" "/algo/problem"
probe_route "登录接口"   "$PUBLIC_WEB_CT" "/api/login" POST
probe_route "提交接口"   "$PUBLIC_WEB_CT" "/api/submit-problem-judge" POST
probe_route "HOJ 前端壳" "$VUE_CT" "/algo/"

# ---------------------------------------------------------------- 8. 测试数据
echo
echo "-- 8. 比赛题测试数据完整性 --"
if [ "${#PROBLEM_IDS[@]}" -eq 0 ]; then
  warn "未传 problem ID，跳过测试数据检查（可用 --contest-id 或 --problem-ids）"
else
  for pid in "${PROBLEM_IDS[@]}"; do
    row="$(mysql_q "SELECT (SELECT COUNT(*) FROM problem_case WHERE pid=$pid AND status=0),
                           (SELECT COUNT(*) FROM problem_case WHERE pid=$pid AND status=0
                              AND (COALESCE(input,'')='' OR COALESCE(output,'')='')),
                           (SELECT COUNT(*) FROM problem_case WHERE pid=$pid AND status=0
                              AND (input LIKE '%.in' OR input LIKE '%.txt')),
                           (SELECT COALESCE(LEFT(title,24),'') FROM problem WHERE id=$pid),
                           (SELECT COUNT(*) FROM problem_case WHERE pid=$pid AND status=0
                              AND (COALESCE(input,'')='' OR COALESCE(output,'')='')
                              AND id=(SELECT MIN(id) FROM problem_case WHERE pid=$pid AND status=0)),
                           (SELECT COUNT(*) FROM problem_case WHERE pid=$pid AND status=0
                              AND COALESCE(input,'')='');" | tr '\t' '|')"
    db_cnt="$(printf '%s' "$row" | cut -d'|' -f1)"
    empty_cnt="$(printf '%s' "$row" | cut -d'|' -f2)"
    fname_cnt="$(printf '%s' "$row" | cut -d'|' -f3)"
    title="$(printf '%s' "$row" | cut -d'|' -f4)"
    first_empty="$(printf '%s' "$row" | cut -d'|' -f5)"
    empty_in="$(printf '%s' "$row" | cut -d'|' -f6)"

    if ! [[ "$db_cnt" =~ ^[1-9][0-9]*$ ]]; then
      fail "题目 $pid($title): 数据库无可用测试点"
      continue
    fi
    # 首个测试点决定 HOJ 的数据模式判定（内联 or 文件式），它不能为空
    [ "${first_empty:-0}" = "0" ] \
      || fail "题目 $pid($title): 首个测试点输入/输出为空（会导致 HOJ 模式判定错误）"
    [ "${empty_in:-0}" = "0" ] \
      || warn "题目 $pid($title): 有 $empty_in 个测试点输入为空（请人工确认是否合法）"
    [ "${empty_cnt:-0}" = "0" ] \
      || warn "题目 $pid($title): 有 $empty_cnt 个测试点输出为空（区间内无解时可能合法，请人工确认）"

    dir="/judge/test_case/problem_${pid}"
    if [ "$fname_cnt" -gt 0 ]; then
      # 文件式（zip 上传）：数据库只存文件名，必须真实落盘，否则必然 System Error
      detail="$(timeout "${TIMEOUT_SECONDS}s" docker exec "$JUDGE_CT" sh -c '
        d="$1"
        [ -d "$d" ] || { echo "目录不存在（数据库为文件式测试数据，但磁盘无该目录）"; exit 1; }
        ins=0; outs=0
        for f in "$d"/*.in; do [ -e "$f" ] || continue; ins=$((ins+1)); b=${f%.in}
          { [ -f "$b.out" ] || [ -f "$b.ans" ]; } || { echo "$(basename "$f") 缺少对应输出"; exit 1; }; done
        for f in "$d"/*.out "$d"/*.ans; do [ -e "$f" ] && outs=$((outs+1)); done
        [ "$ins" -gt 0 ] || { echo "目录存在但无 .in 文件"; exit 1; }
        [ "$outs" -ge "$ins" ] || { echo "输出文件少于输入文件"; exit 1; }
        [ -r "$d" ] || { echo "目录不可读"; exit 1; }
        echo "$ins 对输入输出，可读"
      ' sh "$dir" 2>&1)"
      if [ "$?" -eq 0 ]; then
        ok "题目 $pid($title): 文件式测试数据完整（$detail）"
      else
        fail "题目 $pid($title): 文件式测试数据缺失 → $detail（判题将报 System Error）"
      fi
    else
      if timeout "${TIMEOUT_SECONDS}s" docker exec "$JUDGE_CT" sh -c "[ -r '$dir' ] || [ -w '$(dirname "$dir")' ]" 2>/dev/null; then
        ok "题目 $pid($title): 内联测试数据 $db_cnt 个可用，数据卷可读写"
      else
        fail "题目 $pid($title): 测试数据卷不可读写（$dir）"
      fi
    fi
  done
fi

# ---------------------------------------------------------------- 9. 端到端试判
echo
echo "-- 9. 端到端试判（真实提交并等待终态） --"
if [ "$E2E_ENABLED" != "1" ]; then
  warn "未开启端到端试判（设 PREFLIGHT_E2E=1 并提供 HOJ_E2E_USER/PASS/PID）"
elif [ -z "$E2E_USER" ] || [ -z "$E2E_PASS" ] || [ -z "$E2E_PID" ]; then
  fail "PREFLIGHT_E2E=1 但缺少 HOJ_E2E_USER / HOJ_E2E_PASS / HOJ_E2E_PID"
else
  jq_esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
  e2e_code='#include <iostream>\nint main(){int a=0,b=0;if(std::cin>>a>>b){std::cout<<a+b<<std::endl;}else{std::cout<<0<<std::endl;}return 0;}'
  login_raw="$(timeout "$E2E_TIMEOUT_SECONDS" docker exec "$PUBLIC_WEB_CT" sh -c \
    "curl -s -i -X POST 'http://localhost/api/login' -H 'Content-Type: application/json' \
     -d '{\"username\":\"$(jq_esc "$E2E_USER")\",\"password\":\"$(jq_esc "$E2E_PASS")\"}'" 2>/dev/null)"
  token="$(printf '%s' "$login_raw" | tr -d '\r' | sed -n 's/^[Aa]uthorization: *//p' | head -1)"
  [ -n "$token" ] || token="$(printf '%s' "$login_raw" | sed -n 's/.*"token"[^"]*"\([^"]*\)".*/\1/p' | head -1)"
  if [ -z "$token" ]; then
    fail "试判账号登录失败（检查 HOJ_E2E_USER/PASS 与 /api/login）"
  else
    ok "试判账号登录成功"
    # 显式携带 isRemote，与前端 Problem.vue 的真实请求保持一致；
    # 后端同时兼容该字段缺省并按本地判题处理。cid 非比赛提交传 0。
    submit_raw="$(timeout "$E2E_TIMEOUT_SECONDS" docker exec "$PUBLIC_WEB_CT" sh -c \
      "curl -s -X POST 'http://localhost/api/submit-problem-judge' \
       -H 'Content-Type: application/json' -H 'Authorization: $token' \
       -d '{\"pid\":$E2E_PID,\"cid\":0,\"language\":\"$E2E_LANG\",\"isRemote\":false,\"code\":\"$e2e_code\"}'" 2>/dev/null)"
    submit_id="$(printf '%s' "$submit_raw" | sed -n 's/.*"submitId":\([0-9]\{1,\}\).*/\1/p' | head -1)"
    if [ -z "$submit_id" ]; then
      fail "试判提交失败（pid=$E2E_PID）：$(printf '%s' "$submit_raw" | head -c 200)"
    else
      ok "已提交试判 submitId=$submit_id，等待终态…"
      status=""
      deadline=$((SECONDS + E2E_TIMEOUT_SECONDS))
      while [ "$SECONDS" -lt "$deadline" ]; do
        detail_raw="$(timeout "$TIMEOUT_SECONDS" docker exec "$PUBLIC_WEB_CT" sh -c \
          "curl -s 'http://localhost/api/get-submission-detail?submitId=$submit_id' -H 'Authorization: $token'" 2>/dev/null)"
        status="$(printf '%s' "$detail_raw" | sed -n 's/.*"status":\(-\{0,1\}[0-9]\{1,\}\).*/\1/p' | head -1)"
        case "$status" in 5|6|7|9) sleep 3 ;; "") sleep 3 ;; *) break ;; esac
      done
      if [ -z "$status" ]; then
        fail "试判 submitId=$submit_id 超时未取得结果"
      elif [ "$status" = "4" ]; then
        fail "试判 submitId=$submit_id 结果为 System Error（4）——测试数据或判题链路异常"
      else
        ok "试判 submitId=$submit_id 到达终态 status=$status（非 System Error，判题链路可用）"
      fi
    fi
  fi
fi

# ---------------------------------------------------------------- 汇总
echo
echo "== 汇总: FAIL=$FAIL WARN=$WARN =="
if [ "$FAIL" -eq 0 ]; then
  echo "PASS：可以开赛"
  exit 0
fi
echo "FAIL：禁止开赛（共 $FAIL 项）"
exit 1
