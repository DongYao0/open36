#!/bin/sh
set -eu

config=/etc/frp/frpc.toml
status_output="$(/usr/local/bin/frpc status -c "$config" 2>&1)"

printf '%s\n' "$status_output" \
  | grep -Eq 'open436-public-web[[:space:]]+running'
curl --fail --silent --show-error \
  --connect-timeout 2 --max-time 3 \
  http://open436-prod-public-web/ >/dev/null
