#!/usr/bin/env bash
set -euo pipefail

DOC_PATH="$1"
LOG="/srv/cockswain-core/logs/index_doc_meili.log"

mkdir -p "$(dirname "$LOG")"

MEILI_HOST="${MEILI_HOST:-http://127.0.0.1:7700}"
MEILI_INDEX="${MEILI_INDEX:-docs}"
MEILI_KEY="${MEILI_KEY:-}"

if [ ! -f "$DOC_PATH" ]; then
  echo "$(date '+%F %T') ERROR: file not found: $DOC_PATH" | tee -a "$LOG"
  exit 1
fi

FILENAME=$(basename "$DOC_PATH")
DIRNAME=$(dirname "$DOC_PATH")

# 讀內容（暫時用 cat）
CONTENT="$(cat "$DOC_PATH" 2>/dev/null || true)"

if [ -z "$CONTENT" ]; then
  echo "$(date '+%F %T') WARN: empty content, skip: $DOC_PATH" | tee -a "$LOG"
  exit 0
fi

# 用檔案完整路徑產生一個穩定的 id
DOC_ID=$(printf "%s" "$DOC_PATH" | md5sum | awk '{print $1}')

JSON_PAYLOAD=$(python3 - << PY
import json
content = """$CONTENT"""
if len(content) > 8000:
    content = content[:8000]
doc = {
    "id": "$DOC_ID",
    "filename": "$FILENAME",
    "path": "$DIRNAME",
    "content": content,
}
print(json.dumps(doc))
PY
)

# 送到 meili
if [ -n "$MEILI_KEY" ]; then
  curl -s -X POST "$MEILI_HOST/indexes/$MEILI_INDEX/documents" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $MEILI_KEY" \
    --data "$JSON_PAYLOAD" >> "$LOG" 2>&1 || true
else
  curl -s -X POST "$MEILI_HOST/indexes/$MEILI_INDEX/documents" \
    -H "Content-Type: application/json" \
    --data "$JSON_PAYLOAD" >> "$LOG" 2>&1 || true
fi

echo "$(date '+%F %T') indexed to meili: $DOC_PATH" | tee -a "$LOG"
