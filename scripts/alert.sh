#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"

NODE_IP=$(ip -4 addr show | awk '/inet / && $2 !~ /127\.0\.0\.1/ && $2 !~ /169\.254\./ {split($2,a,"/"); print a[1]; exit}')

# 預設
ALERT_SOURCE="${1:-unknown}"
ALERT_LEVEL="${2:-warn}"
ALERT_MSG="${3:-no message}"

# 讀 .env
if [ -f "$ENV_FILE" ]; then
  set -a
  grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' > /tmp/cockswain-env.$$
  . /tmp/cockswain-env.$$
  rm /tmp/cockswain-env.$$
  set +a
fi

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_ROOT_USER="${MYSQL_ROOT_USER:-root}"
: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD missing in .env}"
: "${MYSQL_DATABASE:?MYSQL_DATABASE missing in .env}"

# 1) 先寫 DB
mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
  -e "USE \`$MYSQL_DATABASE\`; INSERT INTO alerts (node_ip, source, level, message) VALUES ('$NODE_IP', '$ALERT_SOURCE', '$ALERT_LEVEL', '$(printf "%s" "$ALERT_MSG" | sed "s/'/''/g")');" || true

# 2) 再打 webhook（有的話）
if [ -n "${ALERT_WEBHOOK:-}" ]; then
  curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"text\": \"[$NODE_IP][$ALERT_SOURCE][$ALERT_LEVEL] $ALERT_MSG\"}" \
    "$ALERT_WEBHOOK" >/dev/null 2>&1 || true
fi
