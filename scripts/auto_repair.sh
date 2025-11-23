#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
CONF_DIR="$BASE_DIR/conf"
POLICY_FILE="$CONF_DIR/repair_policy.conf"
ALERT_SCRIPT="$BASE_DIR/scripts/alert.sh"

SERVICE_NAME="${1:-}"
NODE_IP=$(ip -4 addr show | awk '/inet / && $2 !~ /127\.0\.0\.1/ && $2 !~ /169\.254\./ {split($2,a,"/"); print a[1]; exit}')

if [ -z "$SERVICE_NAME" ]; then
  echo "usage: $0 <service_name>"
  exit 1
fi

if [ ! -f "$POLICY_FILE" ]; then
  echo "policy file not found: $POLICY_FILE"
  exit 0
fi

# 預設動作
ACTION="ignore"
MAX_ATTEMPTS=1

while read -r line; do
  [[ "$line" =~ ^# ]] && continue
  [[ -z "$line" ]] && continue
  name=$(echo "$line" | awk '{print $1}')
  if [ "$name" = "$SERVICE_NAME" ]; then
    ACTION=$(echo "$line" | awk '{print $2}')
    MAX_ATTEMPTS=$(echo "$line" | awk '{print $3}')
    break
  fi
done < "$POLICY_FILE"

if [ "$ACTION" = "ignore" ]; then
  # 記一筆，表示有東西想修但不在策略裡
  [ -x "$ALERT_SCRIPT" ] && "$ALERT_SCRIPT" "auto_repair" "info" "service $SERVICE_NAME is down but policy=ignore"
  exit 0
fi

# 真正修
ok=1
case "$ACTION" in
  restart_systemd)
    if systemctl restart "$SERVICE_NAME"; then
      ok=0
    fi
    ;;
  restart_docker)
    if sudo docker restart "$SERVICE_NAME"; then
      ok=0
    fi
    ;;
  *)
    ;;
esac

if [ $ok -eq 0 ]; then
  [ -x "$ALERT_SCRIPT" ] && "$ALERT_SCRIPT" "auto_repair" "info" "service $SERVICE_NAME on $NODE_IP restarted by auto_repair ($ACTION)"
else
  [ -x "$ALERT_SCRIPT" ] && "$ALERT_SCRIPT" "auto_repair" "error" "service $SERVICE_NAME on $NODE_IP FAILED to restart ($ACTION)"
fi
