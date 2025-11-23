#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
LOG_DIR="$BASE_DIR/logs"
BACKUP_DIR="$BASE_DIR/backup"
RUN_TS=$(date '+%Y%m%d-%H%M%S')
OUT_FILE="$BACKUP_DIR/logs-$RUN_TS.tar.gz"

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

# 沒有 log 也算成功
if [ ! -d "$LOG_DIR" ]; then
  exit 0
fi

tar -czf "$OUT_FILE" -C "$LOG_DIR" .
# 刪掉 7 天前的 tar.gz
find "$BACKUP_DIR" -type f -name "logs-*.tar.gz" -mtime +7 -delete
