#!/bin/sh
set -u

runtime_file="/runtime/${RUNTIME_FILE_NAME:-client-url.json}"
log_pipe=/tmp/cloudflared-output
origin_url="${TUNNEL_ORIGIN_URL:-http://public-web:80}"
watchdog_enabled="${TUNNEL_WATCHDOG_ENABLED:-false}"
watchdog_url="${TUNNEL_WATCHDOG_PUBLIC_URL:-${PUBLIC_CLIENT_URL:-}}"
watchdog_interval="${TUNNEL_WATCHDOG_INTERVAL_SECONDS:-10}"
watchdog_threshold="${TUNNEL_WATCHDOG_FAILURE_THRESHOLD:-2}"
watchdog_grace="${TUNNEL_WATCHDOG_STARTUP_GRACE_SECONDS:-20}"
watchdog_cooldown="${TUNNEL_WATCHDOG_COOLDOWN_SECONDS:-120}"
watchdog_probe_timeout="${TUNNEL_WATCHDOG_PROBE_TIMEOUT_SECONDS:-5}"
watchdog_restart_grace="${TUNNEL_WATCHDOG_RESTART_GRACE_SECONDS:-5}"
watchdog_state_file=/runtime/tunnel-watchdog-last-restart
prometheus_targets_enabled="${PROMETHEUS_TARGETS_ENABLED:-true}"
prometheus_targets_file="/runtime/${PROMETHEUS_TARGETS_FILE_NAME:-prometheus-public-targets.json}"
watchdog_pid=""
named_tunnel=false

validate_uint() {
  case "$2" in
    ''|*[!0-9]*) printf 'watchdog: invalid %s=%s\n' "$1" "$2"; exit 2 ;;
  esac
  if [ "$2" -eq 0 ]; then
    printf 'watchdog: %s must be greater than zero\n' "$1"
    exit 2
  fi
}

validate_uint TUNNEL_WATCHDOG_INTERVAL_SECONDS "$watchdog_interval"
validate_uint TUNNEL_WATCHDOG_FAILURE_THRESHOLD "$watchdog_threshold"
validate_uint TUNNEL_WATCHDOG_STARTUP_GRACE_SECONDS "$watchdog_grace"
validate_uint TUNNEL_WATCHDOG_COOLDOWN_SECONDS "$watchdog_cooldown"
validate_uint TUNNEL_WATCHDOG_PROBE_TIMEOUT_SECONDS "$watchdog_probe_timeout"
validate_uint TUNNEL_WATCHDOG_RESTART_GRACE_SECONDS "$watchdog_restart_grace"

publish_probe_targets() {
  url=${1%/}
  temp_file="${prometheus_targets_file}.tmp"
  case "$prometheus_targets_enabled" in
    true|1|yes)
      if [ -n "$url" ]; then
        printf '[{"targets":["%s/","%s/algo/"],"labels":{"service":"public"}}]\n' \
          "$url" "$url" > "$temp_file"
      else
        printf '[]\n' > "$temp_file"
      fi
      mv "$temp_file" "$prometheus_targets_file"
      ;;
  esac
}

publish_url() {
  url=$1
  source=$2
  status=$3
  updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  temp_file="${runtime_file}.tmp"
  printf '{"url":"%s","source":"%s","status":"%s","updatedAt":"%s"}\n' \
    "$url" "$source" "$status" "$updated_at" > "$temp_file"
  mv "$temp_file" "$runtime_file"
  publish_probe_targets "$url"
}

if [ -n "${PUBLIC_CLIENT_URL:-}" ]; then
  publish_url "$PUBLIC_CLIENT_URL" configured ready
else
  publish_url "" quick starting
fi

if [ -n "${CLOUDFLARE_TUNNEL_ARGS:-}" ]; then
  # The token and flags contain no whitespace-bearing values; split without eval.
  tunnel_args=$CLOUDFLARE_TUNNEL_ARGS
  case " $tunnel_args " in
    *" run --token "*) named_tunnel=true ;;
  esac
  unset CLOUDFLARE_TUNNEL_ARGS
  set -- $tunnel_args
  unset tunnel_args
else
  set -- tunnel --no-autoupdate --protocol quic --url "$origin_url"
fi

# Named Tunnel 会自行维护多条 edge 连接并重连。公网探测可能受 Cloudflare
# edge 或校园网瞬时抖动影响，不能据此杀掉共享 connector。
if [ "$named_tunnel" = true ]; then
  case "$watchdog_enabled" in
    true|1|yes)
      printf 'watchdog: disabled for named tunnel; cloudflared manages edge reconnects\n'
      watchdog_enabled=false
      ;;
  esac
fi

run_watchdog() {
  sleep "$watchdog_grace"
  failures=0
  while kill -0 "$cloudflared_pid" 2>/dev/null; do
    if ! wget -q --timeout=10 -O /dev/null "$origin_url"; then
      printf 'watchdog: origin unavailable; tunnel restart suppressed\n'
      failures=0
    else
      case "$watchdog_url" in
        *\?*) probe_url="${watchdog_url}&tunnel_watchdog=$(date +%s)" ;;
        *) probe_url="${watchdog_url}?tunnel_watchdog=$(date +%s)" ;;
      esac
      if wget -q --timeout="$watchdog_probe_timeout" -O /dev/null "$probe_url"; then
        if [ "$failures" -gt 0 ]; then
          printf 'watchdog: public endpoint recovered after %s failure(s)\n' "$failures"
        fi
        failures=0
      else
        failures=$((failures + 1))
        printf 'watchdog: public endpoint failed (%s/%s)\n' \
          "$failures" "$watchdog_threshold"
        if [ "$failures" -ge "$watchdog_threshold" ]; then
          now=$(date +%s)
          last_restart=0
          if [ -f "$watchdog_state_file" ]; then
            IFS= read -r last_restart < "$watchdog_state_file" || last_restart=0
          fi
          case "$last_restart" in ''|*[!0-9]*) last_restart=0 ;; esac
          if [ $((now - last_restart)) -ge "$watchdog_cooldown" ]; then
            printf '%s\n' "$now" > "${watchdog_state_file}.tmp"
            mv "${watchdog_state_file}.tmp" "$watchdog_state_file"
            publish_url "$watchdog_url" configured restarting
            printf 'watchdog: restarting cloudflared after consecutive public failures\n'
            kill -TERM "$cloudflared_pid" 2>/dev/null || true
            waited=0
            while kill -0 "$cloudflared_pid" 2>/dev/null \
              && [ "$waited" -lt "$watchdog_restart_grace" ]; do
              sleep 1
              waited=$((waited + 1))
            done
            if kill -0 "$cloudflared_pid" 2>/dev/null; then
              printf 'watchdog: graceful shutdown timed out; forcing restart\n'
              kill -KILL "$cloudflared_pid" 2>/dev/null || true
            fi
            return
          fi
          printf 'watchdog: restart suppressed by cooldown\n'
          failures=0
        fi
      fi
    fi
    sleep "$watchdog_interval"
  done
}

rm -f "$log_pipe"
mkfifo "$log_pipe"
cloudflared "$@" > "$log_pipe" 2>&1 &
cloudflared_pid=$!

terminate() {
  kill -TERM "$cloudflared_pid" 2>/dev/null || true
  if [ -n "$watchdog_pid" ]; then
    kill -TERM "$watchdog_pid" 2>/dev/null || true
  fi
}
trap terminate INT TERM HUP

while IFS= read -r line; do
  printf '%s\n' "$line"
  case "$line" in
    *https://*.trycloudflare.com*)
      detected_url=$(printf '%s\n' "$line" | sed -n 's#.*\(https://[-a-zA-Z0-9.]*\.trycloudflare\.com\).*#\1#p')
      if [ -n "$detected_url" ]; then
        publish_url "$detected_url" quick ready
      fi
      ;;
  esac
done < "$log_pipe" &
reader_pid=$!

case "$watchdog_enabled" in
  true|1|yes)
    if [ -n "$watchdog_url" ]; then
      run_watchdog &
      watchdog_pid=$!
      printf 'watchdog: enabled url=%s interval=%ss threshold=%s cooldown=%ss\n' \
        "$watchdog_url" "$watchdog_interval" "$watchdog_threshold" "$watchdog_cooldown"
    else
      printf 'watchdog: disabled because no public URL is configured\n'
    fi
    ;;
esac

wait "$cloudflared_pid"
exit_code=$?
if [ -n "$watchdog_pid" ]; then
  kill -TERM "$watchdog_pid" 2>/dev/null || true
  wait "$watchdog_pid" 2>/dev/null || true
fi
wait "$reader_pid" 2>/dev/null || true
exit "$exit_code"
