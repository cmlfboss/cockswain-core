#!/usr/bin/env bash
LOG_FILE="/srv/cockswain-core/logs/import-tasks.log"
MAX_SIZE=$((1024*1024))  # 1MB

if [ -f "$LOG_FILE" ]; then
  SIZE=$(stat -c%s "$LOG_FILE")
  if [ "$SIZE" -gt "$MAX_SIZE" ]; then
    tail -n 200 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
  fi
fi
