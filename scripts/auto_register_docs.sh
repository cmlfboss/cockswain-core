#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core/docs"
LOG="/srv/cockswain-core/logs/auto_register_docs.log"
REGISTER_SCRIPT="/srv/cockswain-core/scripts/register_doc.sh"

mkdir -p "$(dirname "$LOG")"

# 掃描指定資料夾底下所有檔案（只掃描一次層級，可自行改成 -maxdepth 2）
find "$BASE_DIR" -type f | while read -r file; do
  # 跳過暫存檔或壓縮檔
  case "$file" in
    *.tmp|*.tar.gz|*.zip|*.log) continue ;;
  esac

  # 登記檔案
  "$REGISTER_SCRIPT" "$file" >> "$LOG" 2>&1
done

echo "$(date '+%F %T') auto-scan finished" | tee -a "$LOG"
