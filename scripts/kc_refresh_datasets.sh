#!/bin/bash
# KC Dynamic Datasets Refresh v1.0
# Role  : 自動刷新所有啟用中的動態資料集（手動維護清單版）
# Owner : L7 / 舵手
# Safe  : 只讀 DB、只寫 snapshot，不動原始資料

set -euo pipefail

AI_CORE_DIR="/srv/cockswain-core/ai-core"
cd "$AI_CORE_DIR"

# 目前已存在的 dataset（之後要加新的，直接往這裡 append）
DATASETS=(
  "kc_recent_api_changes"
)

echo "[kc-refresh] 開始刷新動態資料集..."
python3 -m knowledge_center.dynamic_sets list || true
echo "----------------------------------------"

for code in "${DATASETS[@]}"; do
    echo "[kc-refresh] build ${code} ..."
    python3 -m knowledge_center.dynamic_sets build "$code"
done

echo "[kc-refresh] 所有資料集刷新完畢。"
