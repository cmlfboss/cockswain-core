#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <query>"
  exit 1
fi

QUERY="$1"

MEILI_HOST="${MEILI_HOST:-http://127.0.0.1:7700}"
MEILI_INDEX="${MEILI_INDEX:-docs}"
MEILI_KEY="${MEILI_KEY:-}"

# 呼叫 meili
if [ -n "$MEILI_KEY" ]; then
  RESP=$(curl -s -G "$MEILI_HOST/indexes/$MEILI_INDEX/search" \
    -H "Authorization: Bearer $MEILI_KEY" \
    --data-urlencode "q=$QUERY" \
    --data-urlencode "limit=20")
else
  RESP=$(curl -s -G "$MEILI_HOST/indexes/$MEILI_INDEX/search" \
    --data-urlencode "q=$QUERY" \
    --data-urlencode "limit=20")
fi

python3 - << PY
import json, sys
data = json.loads("""$RESP""")
hits = data.get("hits", [])
if not hits:
    print("no results")
    sys.exit(0)
for i, h in enumerate(hits, 1):
    fn = h.get("filename", "(no name)")
    path = h.get("path", "")
    print(f"[{i}] {fn}  ({path})")
    snippet = h.get("content", "")
    if len(snippet) > 120:
        snippet = snippet[:120] + "..."
    print(f"    {snippet}")
PY
