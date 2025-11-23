#!/usr/bin/env bash
# 自動修復腳本：若 cockswain-core 容器不在，就重啟
set -e

SERVICE="cockswain-core"
LOG="/srv/cockswain-core/logs/self_repair.log"
mkdir -p "$(dirname "$LOG")"

if ! docker ps --format '{{.Names}}' | grep -q "^${SERVICE}$"; then
  echo "$(date) - ${SERVICE} is not running, trying to start..." >> "$LOG"
  docker start "$SERVICE" >> "$LOG" 2>&1 || docker compose -f /srv/cockswain-core/docker-compose.yml up -d >> "$LOG" 2>&1
else
  echo "$(date) - ${SERVICE} is healthy." >> "$LOG"
fi
