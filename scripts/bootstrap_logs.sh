#!/bin/bash
# Cockswain Logs Bootstrap v1.1
# Role  : 建立 / 修正母機 logs 目錄與基本權限（可安全重複執行）
# Owner : L7 / 舵手
# Safe  : idempotent

set -euo pipefail

BASE_DIR="/srv/cockswain-core"
LOG_DIR="$BASE_DIR/logs"
AI_LOG_DIR="$LOG_DIR/ai-core"
SNAP_DIR="$AI_LOG_DIR/snapshots"

echo "[logs-bootstrap] BASE_DIR = $BASE_DIR"
echo "[logs-bootstrap] LOG_DIR  = $LOG_DIR"

# 1) 建立基礎 logs 目錄結構
mkdir -p "$LOG_DIR"
mkdir -p "$AI_LOG_DIR"
mkdir -p "$SNAP_DIR"

# 2) 權限處理
if [ "$(id -u)" -eq 0 ]; then
    echo "[logs-bootstrap] 目前為 root，執行 chown..."
    chown -R cocksmain:cocksmain "$LOG_DIR"
else
    echo "[logs-bootstrap] 非 root（$(whoami)），略過 chown。"
fi

chmod 750 "$LOG_DIR"
chmod 750 "$AI_LOG_DIR"
chmod 750 "$SNAP_DIR"

echo "[logs-bootstrap] 完成 logs 目錄初始化與權限處理。"
