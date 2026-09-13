#!/bin/sh
set -u

runtime_file=/runtime/client-url.json
log_pipe=/tmp/cloudflared-output

publish_url() {
  url=$1
  source=$2
  status=$3
  updated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  temp_file="${runtime_file}.tmp"
  printf '{"url":"%s","source":"%s","status":"%s","updatedAt":"%s"}\n' \
    "$url" "$source" "$status" "$updated_at" > "$temp_file"
  mv "$temp_file" "$runtime_file"
}

if [ -n "${PUBLIC_CLIENT_URL:-}" ]; then
  publish_url "$PUBLIC_CLIENT_URL" configured ready
else
  publish_url "" quick starting
fi

if [ -n "${CLOUDFLARE_TUNNEL_ARGS:-}" ]; then
  # The token and flags contain no whitespace-bearing values; split without eval.
  set -- $CLOUDFLARE_TUNNEL_ARGS
else
  set -- tunnel --no-autoupdate --protocol http2 --url http://public-web:80
fi

rm -f "$log_pipe"
mkfifo "$log_pipe"
cloudflared "$@" > "$log_pipe" 2>&1 &
cloudflared_pid=$!

terminate() {
  kill -TERM "$cloudflared_pid" 2>/dev/null || true
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

wait "$cloudflared_pid"
exit_code=$?
wait "$reader_pid" 2>/dev/null || true
exit "$exit_code"
