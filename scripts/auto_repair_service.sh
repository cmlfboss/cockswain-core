#!/usr/bin/env bash
# auto_repair_service.sh <service_name>
# 專門幫 L6 重啟 cockswain-* 的 systemd 服務

SERVICE="$1"
LOG="/srv/cockswain-core/logs/auto_repair_service.log"
mkdir -p "$(dirname "$LOG")"

ts="$(date +%Y-%m-%dT%H:%M:%S)"

if [[ -z "$SERVICE" ]]; then
  echo "usage: $0 <service_name>" >&2
  exit 1
fi

# 沒帶 .service 幫你補上
if [[ "$SERVICE" != *.service ]]; then
  SERVICE="${SERVICE}.service"
fi

echo "[$ts] restart $SERVICE" >> "$LOG"

# 查真的有這個 service（抓第一欄避免對齊空白）
if ! systemctl list-units --type=service --all | awk '{print $1}' | grep -qx "$SERVICE"; then
  echo "[$ts] service $SERVICE not found" >> "$LOG"
  exit 2
fi

# 先試不用 sudo
if systemctl restart "$SERVICE" >> "$LOG" 2>&1; then
  echo "[$ts] service $SERVICE restarted OK" >> "$LOG"
  exit 0
fi

# 再試 sudo
if sudo systemctl restart "$SERVICE" >> "$LOG" 2>&1; then
  echo "[$ts] service $SERVICE restarted OK (with sudo)" >> "$LOG"
  exit 0
fi

rc=$?
echo "[$ts] service $SERVICE restart FAILED rc=$rc" >> "$LOG"
exit $rc
