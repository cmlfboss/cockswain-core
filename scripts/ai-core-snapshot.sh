#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date -Iseconds)"
OUT_DIR="/srv/cockswain-core/logs/ai-core/snapshots"
OUT_FILE="$OUT_DIR/ai-core-$STAMP.log"

# 確保快照目錄存在
mkdir -p "$OUT_DIR"

{
  echo "==== AI-CORE SNAPSHOT @ $STAMP ===="
  echo "Host: $(hostname)"
  echo

  for svc in \
    cockswain-hybrid.service \
    cockswain-l7.service \
    cockswain-arbiter.service \
    cockswain-reflect.service
  do
    echo "----- $svc -----"
    echo "enabled: $(systemctl is-enabled "$svc" 2>/dev/null || echo "unknown")"
    echo "status : $(systemctl is-active "$svc" 2>/dev/null || echo "unknown")"
    echo "last logs:"
    journalctl -u "$svc" -n 5 --no-pager 2>/dev/null || true
    echo
  done
} >"$OUT_FILE"

echo "snapshot written to: $OUT_FILE"
