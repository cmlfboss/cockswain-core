#!/usr/bin/env bash
set -euo pipefail

WATCH_DIR="/srv/cockswain-core/docs"
REGISTER_SCRIPT="/srv/cockswain-core/scripts/register_doc.sh"
INDEX_SCRIPT="/srv/cockswain-core/scripts/index_doc_meili.sh"
LOG="/srv/cockswain-core/logs/watch_docs.log"

mkdir -p "$(dirname "$LOG")"

echo "$(date '+%F %T') INFO: watch_docs started, watching $WATCH_DIR" | tee -a "$LOG"

inotifywait -m -r -e create -e moved_to -e close_write "$WATCH_DIR" | while read -r path action file; do
  fullpath="${path%/}/$file"

  case "$fullpath" in
    *.swp|*.tmp|*.tar.gz|*.zip)
      continue
      ;;
  esac

  if [ -f "$fullpath" ]; then
    echo "$(date '+%F %T') INFO: detected $action on $fullpath" | tee -a "$LOG"

    # 1) 登記到資料庫
    "$REGISTER_SCRIPT" "$fullpath" >> "$LOG" 2>&1 || true

    # 2) 索引到本地搜尋引擎（若有開）
    if [ -x "$INDEX_SCRIPT" ]; then
      "$INDEX_SCRIPT" "$fullpath" >> "$LOG" 2>&1 || true
    fi
  fi
done
