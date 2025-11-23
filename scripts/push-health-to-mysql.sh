#!/usr/bin/env bash
set -e

ENV_FILE="/srv/cockswain-core/.env.local"
if [ ! -f "$ENV_FILE" ]; then
  echo "[push-health-mysql] env file not found: $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

LOG_FILE="/srv/cockswain-core/logs/observer/health.log"
if [ ! -f "$LOG_FILE" ]; then
  echo "[push-health-mysql] log file not found: $LOG_FILE"
  exit 0
fi

SQL_FILE="/tmp/push-health.sql"
echo "USE ${MYSQL_HEALTH_DB};" > "$SQL_FILE"

tail -n 200 "$LOG_FILE" | while read -r line; do
  [ -z "$line" ] && continue
  ts=$(echo "$line" | awk '{print $1" "$2}')
  cpu=$(echo "$line" | grep -o 'cpu_temp=[^ ]*' | cut -d= -f2)
  disk=$(echo "$line" | grep -o 'disk_usage=[^ ]*' | cut -d= -f2)
  warn=$(echo "$line" | grep -o 'warn=[^ ]*' | cut -d= -f2)

  [ -z "$warn" ] && warn=0
  cpu_clean=$(echo "$cpu" | tr -d '°C')

  echo "INSERT INTO system_state (timestamp, cpu_temp, disk_usage, warn, note) VALUES ('$ts', '$cpu_clean', '$disk', $warn, 'ingest');" >> "$SQL_FILE"
done

# 優先走 UNIX socket（就是你用 sudo mysql 那顆）
if [ -n "$MYSQL_HEALTH_SOCKET" ] && [ -S "$MYSQL_HEALTH_SOCKET" ]; then
  mysql --socket="$MYSQL_HEALTH_SOCKET" \
        -u "$MYSQL_HEALTH_USER" \
        -p"$MYSQL_HEALTH_PASSWORD" \
        < "$SQL_FILE"
else
  # 沒有 socket 再走 TCP
  mysql -h "$MYSQL_HEALTH_HOST" \
        -P "$MYSQL_HEALTH_PORT" \
        -u "$MYSQL_HEALTH_USER" \
        -p"$MYSQL_HEALTH_PASSWORD" \
        < "$SQL_FILE"
fi

echo "[push-health-mysql] inserted at $(date '+%F %T')"
