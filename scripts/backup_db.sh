#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"
BACKUP_DIR="$BASE_DIR/backup"
LOG_DIR="$BASE_DIR/logs"
LOG="$LOG_DIR/backup_db.log"

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "$(date '+%F %T') ERROR: missing $ENV_FILE" | tee -a "$LOG"
  exit 1
fi

# 載入 .env
set -a
grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' > /tmp/cockswain-env.$$
. /tmp/cockswain-env.$$
rm /tmp/cockswain-env.$$
set +a

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_ROOT_USER="${MYSQL_ROOT_USER:-root}"
: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD missing in .env}"
: "${MYSQL_DATABASE:?MYSQL_DATABASE missing in .env}"

TS=$(date '+%Y%m%d-%H%M%S')
OUT_FILE="$BACKUP_DIR/${MYSQL_DATABASE}-${TS}.sql"

# 做 dump
mysqldump -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
  --databases "$MYSQL_DATABASE" > "$OUT_FILE"

echo "$(date '+%F %T') INFO: dumped to $OUT_FILE" | tee -a "$LOG"

# 刪 7 天前的舊檔
find "$BACKUP_DIR" -type f -name "${MYSQL_DATABASE}-*.sql" -mtime +7 -print -delete >> "$LOG" 2>&1 || true
