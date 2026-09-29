#!/usr/bin/env bash
set -u

readonly CONNECTOR_SERVICE="open436-cloudflared.service"
readonly DISABLE_FILE="/etc/open436-relay-health-guard.disabled"
readonly PAGE_URL="http://127.0.0.1:18080/"
readonly API_URL="http://127.0.0.1:18080/api/users/homepage/public"
readonly INTERVAL_SECONDS=5
readonly FAILURE_THRESHOLD=3
readonly RECOVERY_THRESHOLD=6
readonly ACTION_COOLDOWN_SECONDS=60

failure_count=0
success_count=0
last_action_epoch=0

log() {
  printf '%s %s\n' "$(date --iso-8601=seconds)" "$*"
}

probe_url() {
  local url="$1"
  local code
  code="$(curl --silent --output /dev/null \
    --write-out '%{http_code}' --connect-timeout 2 --max-time 3 "$url")" || return 1
  [[ "$code" == "200" ]]
}

origin_is_healthy() {
  probe_url "$PAGE_URL" && probe_url "$API_URL"
}

cooldown_elapsed() {
  local now
  now="$(date +%s)"
  (( now - last_action_epoch >= ACTION_COOLDOWN_SECONDS ))
}

log "relay health guard started"

if [[ "${1:-}" == "--check" ]]; then
  if origin_is_healthy; then
    log "origin check passed"
    exit 0
  fi
  log "origin check failed"
  exit 1
fi

while true; do
  if [[ -e "$DISABLE_FILE" ]]; then
    failure_count=0
    success_count=0
    sleep "$INTERVAL_SECONDS"
    continue
  fi

  if origin_is_healthy; then
    failure_count=0
    if systemctl is-active --quiet "$CONNECTOR_SERVICE"; then
      success_count=0
    else
      ((success_count += 1))
      if (( success_count >= RECOVERY_THRESHOLD )) && cooldown_elapsed; then
        if systemctl start "$CONNECTOR_SERVICE"; then
          last_action_epoch="$(date +%s)"
          success_count=0
          log "origin recovered; connector started"
        else
          log "failed to start connector; will retry"
        fi
      fi
    fi
  else
    success_count=0
    ((failure_count += 1))
    if (( failure_count == 1 \
      || failure_count == FAILURE_THRESHOLD \
      || failure_count % 12 == 0 )); then
      log "origin probe failed (${failure_count}/${FAILURE_THRESHOLD})"
    fi
    if (( failure_count >= FAILURE_THRESHOLD )) \
      && systemctl is-active --quiet "$CONNECTOR_SERVICE" \
      && cooldown_elapsed; then
      if systemctl stop "$CONNECTOR_SERVICE"; then
        last_action_epoch="$(date +%s)"
        failure_count=0
        log "origin unhealthy; connector stopped"
      else
        log "failed to stop connector; will retry"
      fi
    fi
  fi

  sleep "$INTERVAL_SECONDS"
done
