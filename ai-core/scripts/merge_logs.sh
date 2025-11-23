#!/bin/bash
# Cockswain 標準 Log 彙總入口腳本

set -e

BASE_DIR="/srv/cockswain-core/ai-core"
cd "$BASE_DIR"

# 直接轉呼叫目前的標準 log_merger 程式
python3 "$BASE_DIR/workspace/auto_code/20251121_025659_log_merger.py" "$@"
