#!/usr/bin/env bash
set -u

readonly INTERVAL_SECONDS="${INTERVAL_SECONDS:-5}"
readonly FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"
readonly COOLDOWN_SECONDS="${COOLDOWN_SECONDS:-60}"
readonly STATE_DIR="${STATE_DIR:-$HOME/.local/state/open436-frpc-guard}"

mkdir -p "$STATE_DIR"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*"; }

container_healthy() {
  local container="$1" proxy="$2" health status
  health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container" 2>/dev/null)"
  [[ "$health" == "healthy" ]] || return 1
  status="$(docker exec "$container" /usr/local/bin/frpc status -c /etc/frp/frpc.toml 2>&1)" || return 1
  grep -Eq "${proxy}[[:space:]]+running" <<<"$status"
}

restart_if_needed() {
  local key="$1" container="$2" proxy="$3"
  local count_file="$STATE_DIR/$key.failures" cooldown_file="$STATE_DIR/$key.last_restart"
  local failures=0 last_restart=0 now

  if container_healthy "$container" "$proxy"; then
    rm -f "$count_file"
    return 0
  fi

  [[ -f "$count_file" ]] && failures="$(<"$count_file")"
  failures=$((failures + 1))
  printf '%s' "$failures" >"$count_file"
  (( failures < FAILURE_THRESHOLD )) && return 1

  now="$(date +%s)"
  [[ -f "$cooldown_file" ]] && last_restart="$(<"$cooldown_file")"
  (( now - last_restart < COOLDOWN_SECONDS )) && return 1

  log "restarting unhealthy $key after $failures failed checks"
  if docker restart --time 10 "$container" >/dev/null; then
    printf '%s' "$now" >"$cooldown_file"
    printf '0' >"$count_file"
    log "$key restarted"
  else
    log "failed to restart $key"
  fi
}

run_loop() {
  while true; do
    restart_if_needed primary open436-relay-frpc open436-public-web || true
    restart_if_needed backup open436-relay-frpc-public-backup open436-public-web-backup || true
    sleep "$INTERVAL_SECONDS"
  done
}

case "${1:-run}" in
  run) run_loop ;;
  check)
    container_healthy open436-relay-frpc open436-public-web
    container_healthy open436-relay-frpc-public-backup open436-public-web-backup
    ;;
  *) echo "usage: $0 {run|check}" >&2; exit 2 ;;
esac
