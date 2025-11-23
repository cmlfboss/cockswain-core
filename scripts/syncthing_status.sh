#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"
LOG_DIR="$BASE_DIR/logs"
LOG="$LOG_DIR/syncthing_status.log"

mkdir -p "$LOG_DIR"

# 讀 .env
if [ -f "$ENV_FILE" ]; then
  set -a
  grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' > /tmp/cockswain-env.$$
  . /tmp/cockswain-env.$$
  rm /tmp/cockswain-env.$$
  set +a
fi

# 預設值
MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_ROOT_USER="${MYSQL_ROOT_USER:-root}"
: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD missing in .env}"
: "${MYSQL_DATABASE:?MYSQL_DATABASE missing in .env}"

SYNCTHING_HOST="${SYNCTHING_HOST:-127.0.0.1}"
SYNCTHING_PORT="${SYNCTHING_PORT:-8384}"
SYNCTHING_APIKEY="${SYNCTHING_APIKEY:-}"

# 找出本機 LAN IP（跟 node_scan 用的同一張）
SELF_IP=$(ip -4 addr show | awk '/inet / && $2 !~ /127\.0\.0\.1/ && $2 !~ /169\.254\./ {split($2,a,"/"); print a[1]; exit}')

STATUS="down"
HTTP_CODE=0

# 打 Syncthing
if [ -n "$SYNCTHING_APIKEY" ]; then
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $SYNCTHING_APIKEY" "http://$SYNCTHING_HOST:$SYNCTHING_PORT/rest/system/ping" || true)
else
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$SYNCTHING_HOST:$SYNCTHING_PORT/rest/system/ping" || true)
fi

if [ "$HTTP_CODE" = "200" ]; then
  STATUS="up"
fi

# 寫 DB
mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
  -e "USE \`$MYSQL_DATABASE\`; UPDATE nodes SET syncthing_status='$STATUS', syncthing_checked_at=NOW() WHERE ip='$SELF_IP';"

echo "$(date '+%F %T') ip=$SELF_IP syncthing=$STATUS http=$HTTP_CODE" >> "$LOG"
