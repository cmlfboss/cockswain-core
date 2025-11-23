#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"
LOG_DIR="$BASE_DIR/logs"
ALIVE="$LOG_DIR/node_alive.txt"
LOG="$LOG_DIR/write_nodes_to_db.log"

mkdir -p "$LOG_DIR"

# 1) 檢查 .env
if [ ! -f "$ENV_FILE" ]; then
  echo "$(date '+%F %T') ERROR: missing $ENV_FILE" | tee -a "$LOG"
  exit 1
fi

# 2) 載入 .env（去掉註解與空行）
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

# 3) 沒掃描結果就結束
if [ ! -f "$ALIVE" ]; then
  echo "$(date '+%F %T') INFO: $ALIVE not found, nothing to import" | tee -a "$LOG"
  exit 0
fi

# 4) 先全部標成 inactive
mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
  -e "USE \`$MYSQL_DATABASE\`; UPDATE nodes SET status='inactive';" \
  || { echo "$(date '+%F %T') ERROR: mark inactive failed" | tee -a "$LOG"; exit 1; }

# 5) 逐行 upsert 成 active
while IFS= read -r ip; do
  ip_trimmed="$(echo "$ip" | tr -d '[:space:]')"
  [ -z "$ip_trimmed" ] && continue

  SQL="USE \`$MYSQL_DATABASE\`;
  INSERT INTO nodes (ip, last_seen, status)
  VALUES ('$ip_trimmed', NOW(), 'active')
  ON DUPLICATE KEY UPDATE last_seen=NOW(), status='active';"

  mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
    -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
    -e "$SQL" \
    || echo "$(date '+%F %T') ERROR: upsert $ip_trimmed failed" | tee -a "$LOG"
done < "$ALIVE"

echo "$(date '+%F %T') INFO: import finished" | tee -a "$LOG"

