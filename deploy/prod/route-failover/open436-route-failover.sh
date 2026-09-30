#!/usr/bin/env bash
set -u

readonly CONNECTOR="${CONNECTOR:-open436-prod-cloudflared}"
readonly PRIMARY_URL="${PRIMARY_URL:-https://47.104.67.179/algo/api/users/homepage/public}"
readonly LOCAL_URL="${LOCAL_URL:-http://172.20.193.162:8080/algo/api/users/homepage/public}"
readonly PUBLIC_URL="${PUBLIC_URL:-https://open0436.space/algo/api/users/homepage/public}"
readonly CF_EDGE_IP="${CF_EDGE_IP:-172.67.148.49}"
readonly INTERVAL="${INTERVAL:-5}"
readonly FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"
readonly RECOVERY_THRESHOLD="${RECOVERY_THRESHOLD:-120}"
readonly STATE_DIR="${STATE_DIR:-$HOME/.local/state/open436-route-failover}"
readonly STATE_FILE="$STATE_DIR/state"

mkdir -p "$STATE_DIR"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*"; }

probe() {
  curl --insecure --fail --silent --show-error --output /dev/null \
    --connect-timeout 2 --max-time 4 "$1?route_probe=$(date +%s%N)"
}

connector_running() {
  [[ "$(docker inspect -f '{{.State.Running}}' "$CONNECTOR" 2>/dev/null)" == "true" ]]
}

write_state() {
  local mode="$1" reason="$2" tmp="$STATE_FILE.tmp"
  {
    printf 'mode=%q\n' "$mode"
    printf 'changed_at=%q\n' "$(date --iso-8601=seconds)"
    printf 'reason=%q\n' "$reason"
  } >"$tmp"
  mv "$tmp" "$STATE_FILE"
}

start_backup() {
  local reason="$1"
  if connector_running; then
    write_state backup "$reason"
    return 0
  fi
  if ! probe "$LOCAL_URL"; then
    log "backup suppressed: local origin is unhealthy"
    return 1
  fi
  if docker start "$CONNECTOR" >/dev/null; then
    write_state backup "$reason"
    log "backup connector started: $reason"
    return 0
  fi
  log "failed to start backup connector"
  return 1
}

stop_backup() {
  if connector_running; then
    docker stop --time 30 "$CONNECTOR" >/dev/null || return 1
  fi
  write_state primary "manual failback completed"
  log "backup connector stopped; primary route selected"
}

public_probe() {
  curl --fail --silent --show-error --output /dev/null \
    --resolve "open0436.space:443:$CF_EDGE_IP" \
    --connect-timeout 3 --max-time 8 \
    "$PUBLIC_URL?route_probe=$(date +%s%N)"
}

manual_failback() {
  local i
  for i in 1 2 3 4 5; do
    probe "$PRIMARY_URL" || { log "failback refused: primary probe $i failed"; return 1; }
    sleep 1
  done
  stop_backup || return 1
  sleep 3
  if public_probe; then
    log "failback verified through Cloudflare edge $CF_EDGE_IP"
    return 0
  fi
  log "failback verification failed; restoring backup"
  start_backup "automatic rollback after failed failback"
  return 1
}

show_status() {
  if probe "$PRIMARY_URL"; then echo "primary=healthy"; else echo "primary=unhealthy"; fi
  if probe "$LOCAL_URL"; then echo "local_origin=healthy"; else echo "local_origin=unhealthy"; fi
  if connector_running; then echo "backup_connector=running"; else echo "backup_connector=stopped"; fi
  [[ -f "$STATE_FILE" ]] && sed -n '1,3p' "$STATE_FILE"
}

run_loop() {
  local failures=0 recoveries=0 recovery_notified=false
  log "route failover monitor started"
  while true; do
    if probe "$PRIMARY_URL"; then
      failures=0
      if connector_running; then
        ((recoveries += 1))
        if (( recoveries >= RECOVERY_THRESHOLD )) && [[ "$recovery_notified" == false ]]; then
          log "primary stable for $((RECOVERY_THRESHOLD * INTERVAL))s; manual failback is ready"
          recovery_notified=true
        fi
      else
        recoveries=0
        recovery_notified=false
      fi
    else
      recoveries=0
      recovery_notified=false
      ((failures += 1))
      if (( failures == 1 || failures == FAILURE_THRESHOLD || failures % 12 == 0 )); then
        log "primary probe failed ($failures/$FAILURE_THRESHOLD)"
      fi
      if (( failures >= FAILURE_THRESHOLD )); then
        start_backup "primary failed $failures consecutive probes" || true
      fi
    fi
    sleep "$INTERVAL"
  done
}

case "${1:-status}" in
  run) run_loop ;;
  status) show_status ;;
  failover) start_backup "manual failover" ;;
  failback) manual_failback ;;
  *) echo "usage: $0 {run|status|failover|failback}" >&2; exit 2 ;;
esac
