#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
DOCS_DIR="$BASE_DIR/docs"
BACKUP_DIR="$BASE_DIR/backup"
LOG_DIR="$BASE_DIR/logs"
LOG="$LOG_DIR/backup_docs.log"

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

ts=$(date '+%Y%m%d-%H%M%S')
archive="$BACKUP_DIR/docs-$ts.tar.gz"

tar -czf "$archive" -C "$BASE_DIR" docs

echo "$(date '+%F %T') INFO: docs snapshot -> $archive" >> "$LOG"
