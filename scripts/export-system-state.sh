#!/usr/bin/env bash
set -e

OUT_DIR="/srv/cockswain-core/state"
TMP_TSV="/tmp/system_state.tsv"
SOCKET="/var/run/mysqld/mysqld.sock"

mkdir -p "$OUT_DIR"

# 把整張表吐成純文字 (TSV)
mysql --socket="$SOCKET" -u root \
  -e "SELECT id, timestamp, cpu_temp, disk_usage, warn, source, note FROM cockswain.system_state ORDER BY timestamp DESC;" \
  --batch --skip-column-names > "$TMP_TSV"

# 呼叫轉換的 python
python3 /srv/cockswain-core/scripts/export-system-state.py "$TMP_TSV" "$OUT_DIR/system_state.json"

echo "[export-system-state] wrote $OUT_DIR/system_state.json"
