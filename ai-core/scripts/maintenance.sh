#!/bin/bash
set -e

BASE="/srv/cockswain-core/ai-core"
AC="$BASE/scripts/run_autocoder.py"

TS=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="$BASE/workspace/auto_code"
REPORT="$LOG_DIR/maintenance_${TS}.txt"

mkdir -p "$LOG_DIR"

log() {
    echo "$@" | tee -a "$REPORT"
}

# 從 run_autocoder 輸出中抓出 "=== OUTPUT FILE ===" 下一行的路徑
run_autocode() {
    local prompt="$1"
    log ""
    log "[autocoder] $prompt"

    local tmp
    tmp=$(mktemp)

    # 先讓 autocoder 跑完，把輸出寫進 tmp，順便也寫進報告
    python3 "$AC" "$prompt" >"$tmp" 2>&1
    cat "$tmp" >>"$REPORT"

    # 解析輸出中的 OUTPUT FILE
    local script
    script=$(awk '/^=== OUTPUT FILE ===/{getline; print;}' "$tmp" | tail -n 1)
    rm -f "$tmp"

    if [ -z "$script" ] || [ ! -f "$script" ]; then
        log "[warn] no output script found for: $prompt"
        return
    fi

    log "[run] $script"
    python3 "$script" >>"$REPORT" 2>&1
}

run_autocode_cleanup() {
    local prompt="$1"
    log ""
    log "[autocoder-cleanup] $prompt"

    local tmp
    tmp=$(mktemp)
    python3 "$AC" "$prompt" >"$tmp" 2>&1
    cat "$tmp" >>"$REPORT"

    local script
    script=$(awk '/^=== OUTPUT FILE ===/{getline; print;}' "$tmp" | tail -n 1)
    rm -f "$tmp"

    if [ -z "$script" ] || [ ! -f "$script" ]; then
        log "[warn] no cleanup script found for: $prompt"
        return
    fi

    log "[run cleanup] $script"
    AC_TARGET_DIR="/srv/cockswain-core/backup" \
    AC_FILE_PATTERN="logs-*.tar.gz" \
    AC_MAX_AGE_DAYS=30 \
    AC_CONFIRM="${AC_CONFIRM:-0}" \
    python3 "$script" >>"$REPORT" 2>&1
}

log "[start] maintenance at $(date)"

log "[1] merging logs..."
run_autocode "自動整理日誌檔案"

log "[2] disk health check..."
run_autocode "檢查母機磁碟剩餘空間，並產生詳細報告"

log "[3] find largest files..."
run_autocode "找出 /srv/cockswain-core 底下最大的檔案，列出前 20 個就好"

log "[4] scan old backups (dry-run)..."
run_autocode_cleanup "清理 /srv/cockswain-core/backup 底下 30 天前的 logs-*.tar.gz 備份檔，不要一次全刪，預設先顯示要刪哪些就好"

log "[done] maintenance completed at $(date)"
log "[ok] maintenance finished. report saved: $REPORT"
