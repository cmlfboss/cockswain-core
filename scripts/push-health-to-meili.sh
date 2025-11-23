#!/usr/bin/env bash
set -e

MEILI_ENDPOINT="http://127.0.0.1:7700"
INDEX_NAME="health"
TMP_JSON="/tmp/health-index.json"

/srv/cockswain-core/scripts/log-indexer.py

if ! curl -s "$MEILI_ENDPOINT/health" | grep -q '"status":"available"'; then
  echo "[push-health] Meilisearch not ready"
  exit 1
fi

curl -s -X POST "$MEILI_ENDPOINT/indexes" \
  -H "Content-Type: application/json" \
  --data "{\"uid\": \"$INDEX_NAME\"}" >/dev/null || true

curl -s -X POST "$MEILI_ENDPOINT/indexes/$INDEX_NAME/documents" \
  -H "Content-Type: application/json" \
  --data-binary "@$TMP_JSON" >/dev/null

echo "[push-health] done at $(date '+%F %T')"
