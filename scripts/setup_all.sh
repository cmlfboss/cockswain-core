#!/bin/bash
# Cockswain Mother-Node Setup All v1.0
# Role  : 統一調用所有 bootstrap / 初始化腳本
# Owner : L7 / 舵手
# Modes : 
#   - 無參數      => dry-run（只列出 / 模擬）
#   - run        => real-run（實際執行並記錄 log）

set -euo pipefail

MODE="${1:-dry}"  # 預設 dry-run

BASE_DIR="/srv/cockswain-core"
SCRIPT_DIR="$BASE_DIR/scripts"
LOG_FILE="$BASE_DIR/setup_all_$(date +%Y%m%d_%H%M%S).log"

# 載入環境工具
if [ -f "$SCRIPT_DIR/lib_env.sh" ]; then
    # shellcheck source=/srv/cockswain-core/scripts/lib_env.sh
    source "$SCRIPT_DIR/lib_env.sh"
else
    echo "[setup-all] 找不到 lib_env.sh，請先建立：$SCRIPT_DIR/lib_env.sh"
    exit 1
fi

echo "[setup-all] 啟動 Cockswain 母機 setup-all (mode=$MODE)"
echo "[setup-all] Log: $LOG_FILE"
echo "-----------------------------------------------"

BOOTSTRAPS=()

# 一般 bootstrap
if ls "$SCRIPT_DIR"/bootstrap_*.sh >/dev/null 2>&1; then
  while IFS= read -r f; do BOOTSTRAPS+=("$f"); done < <(ls "$SCRIPT_DIR"/bootstrap_*.sh)
fi

# DB 類 bootstrap
if ls "$SCRIPT_DIR"/db_bootstrap_*.sh >/dev/null 2>&1; then
  while IFS= read -r f; do BOOTSTRAPS+=("$f"); done < <(ls "$SCRIPT_DIR"/db_bootstrap_*.sh)
fi

if [ ${#BOOTSTRAPS[@]} -eq 0 ]; then
    echo "[setup-all] 找不到任何 bootstrap 腳本。"
    exit 0
fi

echo "[setup-all] 找到以下 bootstrap 腳本："
for b in "${BOOTSTRAPS[@]}"; do
    echo "  - $b"
done

echo

if [ "$MODE" = "dry" ]; then
    echo "[setup-all] 開始 dry-run 模擬執行（不會做實際變更）..."
    echo
    for b in "${BOOTSTRAPS[@]}"; do
        echo "[DRY] Would run: $b"
    done
    echo
    echo "[setup-all] dry-run 完成。要實際執行，請使用：setup_all.sh run"
    exit 0
fi

if [ "$MODE" != "run" ]; then
    echo "[setup-all] 未知模式：$MODE"
    echo "用法："
    echo "  setup_all.sh        # dry-run"
    echo "  setup_all.sh run    # real-run"
    exit 1
fi

echo "[setup-all] 進入 real-run 模式，將依序執行所有 bootstrap 腳本。"
echo "[setup-all] 所有輸出會寫入：$LOG_FILE"
echo

for b in "${BOOTSTRAPS[@]}"; do
    echo "[RUN] $b"
    # 確保腳本可執行
    if [ ! -x "$b" ]; then
        chmod +x "$b" || true
    fi
    {
      echo "======== BOOTSTRAP START: $b ========"
      date
      "$b"
      echo "======== BOOTSTRAP END: $b ========"
      echo
    } >> "$LOG_FILE" 2>&1
done

echo
echo "[setup-all] real-run 完成。詳細 log 請查看：$LOG_FILE"
