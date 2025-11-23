#!/usr/bin/env bash
# 簡易自更新：預留，未來可拉私有 registry 或 git
LOG="/srv/cockswain-core/logs/auto_update.log"
mkdir -p "$(dirname "$LOG")"

echo "$(date) - auto update check (placeholder)" >> "$LOG"
