#!/usr/bin/env bash
set -e
echo "[INGEST] h1 ..."
curl -s -X POST http://127.0.0.1:8000/helmsman/h1/ingest-all | jq .
echo "[INGEST] h2 ..."
curl -s -X POST http://127.0.0.1:8000/helmsman/h2/ingest-all | jq .
