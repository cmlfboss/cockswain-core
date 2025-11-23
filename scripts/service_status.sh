#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"
LOG_DIR="$BASE_DIR/logs"
LOG="$LOG_DIR/service_status.log"

mkdir -p "$LOG_DIR"

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

# 找本機 IP，用你現在的 192.168.0.x 那條，跳過 169.254
SELF_IP=$(ip -4 addr show | awk '/inet / && $2 !~ /127\.0\.0\.1/ && $2 !~ /169\.254\./ {split($2,a,"/"); print a[1]; exit}')

# 要檢查的 docker 容器
DOCKER_SERVICES=("cockswain-core")

# 要檢查的 systemd 服務/計時器
SYSTEMD_SERVICES=(
  "cockswain-node-scan.timer"
  "cockswain-node-db.timer"
  "cockswain-syncthing-status.timer"
  "cockswain-metrics.timer"
  "cockswain-service-status.timer"
  "cockswain-inbox-consume.timer"
  "cockswain-backup-db.timer"
  "cockswain-backup-logs.timer"
  "cockswain-health.timer"
)


# 檢查 docker
for svc in "${DOCKER_SERVICES[@]}"; do
  status="down"
  if sudo docker ps --format '{{.Names}}' | grep -q "^${svc}$"; then
    status="up"
  fi
  mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
    -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
    -e "USE \`$MYSQL_DATABASE\`; INSERT INTO services (node_ip, service_name, service_type, status) VALUES ('$SELF_IP', '$svc', 'docker', '$status')
        ON DUPLICATE KEY UPDATE status='$status', checked_at=NOW();"
  echo "$(date '+%F %T') ip=$SELF_IP docker:$svc $status" >> "$LOG"
done

# 檢查 systemd 狀態並寫入資料庫
for svc in "${SYSTEMD_SERVICES[@]}"; do
  status="down"
  if systemctl is-active --quiet "$svc"; then
    status="up"
  fi

  # 寫入 MySQL
  mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
    -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
    -e "USE \`$MYSQL_DATABASE\`;
        INSERT INTO services (node_ip, service_name, service_type, status)
        VALUES ('$SELF_IP', '$svc', 'systemd', '$status')
        ON DUPLICATE KEY UPDATE status='$status', checked_at=NOW();" || true

  # 紀錄日誌
  echo "$(date '+%F %T') ip=$SELF_IP systemd:$svc $status" >> "$LOG"

  # 若服務非 up，觸發告警
  if [ "$status" != "up" ]; then
    /srv/cockswain-core/scripts/alert.sh \
      "service_status" \
      "warn" \
      "systemd service '$svc' on node $SELF_IP is $status"
  fi
done
