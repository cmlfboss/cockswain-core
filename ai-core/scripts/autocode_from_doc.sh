#!/bin/bash
# Cockswain 自動編程入口：從 tempstore doc 產生程式骨架

set -e

BASE_DIR="/srv/cockswain-core/ai-core"
cd "$BASE_DIR"

DOC_ID="$1"

if [ -z "$DOC_ID" ]; then
  echo "[autocode_from_doc] 用法: autocode_from_doc.sh <doc_id>" >&2
  exit 1
fi

python3 -m auto_coder.generator from_doc "$DOC_ID"
