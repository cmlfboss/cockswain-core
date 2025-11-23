#!/usr/bin/env bash
set -e

BASE_DIR="/srv/cockswain-core/ai-core"
EVOL_DIR="$BASE_DIR/l7_evolution"
SQL_FILE="$EVOL_DIR/migrations_l7_evolution_v1.sql"

echo ">>> [1/4] 建立 l7_evolution 目錄結構..."
mkdir -p "$EVOL_DIR"
mkdir -p "$EVOL_DIR/logs"

echo ">>> [2/4] 建立預設設定檔 config_evolution.yaml..."
cat > "$EVOL_DIR/config_evolution.yaml" <<'YAML'
# 舵手自我進化 v1.0 設定檔

# 每次演化週期會掃描的資料來源
sources:
  # 目前先掃對話紀錄 / 任務紀錄的壓縮檔或 log
  dialog_summary_path: "/srv/cockswain-core/logs/dialog_summary.jsonl"
  task_summary_path: "/srv/cockswain-core/logs/task_summary.jsonl"

# 認知循環強度設定（先保守）
cognitive_loop:
  max_items_per_cycle: 50      # 每輪最多處理多少條事件
  min_importance_score: 0.3    # 重要性門檻（0~1），太低就忽略
  adjustment_step: 0.05        # 行為微調步幅（先小一點）

# 自主任務建議設定
self_initiating:
  enable_suggestions: true
  max_suggested_tasks_per_day: 10
  default_priority: 3          # 1=最高, 5=最低

# Evolution Log 記錄相關
evolution_log:
  max_daily_length: 2000       # 單日詳細描述最大字元數（避免爆掉）
YAML

echo ">>> [3/4] 建立 SQL migration 檔案..."
cat > "$SQL_FILE" <<'SQL'
-- l7_evolution_v1 - 新增三張表

CREATE TABLE IF NOT EXISTS l7_evolution_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME NOT NULL,
  category VARCHAR(50) NOT NULL,       -- daily_summary / observation / adjustment / reflection
  title VARCHAR(255) NOT NULL,
  summary TEXT NOT NULL,
  details JSON NULL,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at),
  KEY idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS l7_system_status (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME NOT NULL,
  overall_health VARCHAR(32) NOT NULL,  -- good / warning / critical
  l1_status VARCHAR(32) DEFAULT NULL,
  l2_status VARCHAR(32) DEFAULT NULL,
  l3_status VARCHAR(32) DEFAULT NULL,
  l4_status VARCHAR(32) DEFAULT NULL,
  l5_status VARCHAR(32) DEFAULT NULL,
  l6_status VARCHAR(32) DEFAULT NULL,
  l7_status VARCHAR(32) DEFAULT NULL,
  metrics JSON NULL,                    -- CPU / Mem / 服務狀態 等
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS l7_suggested_tasks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  priority TINYINT UNSIGNED NOT NULL DEFAULT 3, -- 1~5
  status ENUM('suggested','approved','rejected','in_progress','done') NOT NULL DEFAULT 'suggested',
  source VARCHAR(64) NOT NULL,                  -- 'l7_evolution'
  meta JSON NULL,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at),
  KEY idx_status (status),
  KEY idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
SQL

echo ">>> [4/4] 提示：接下來請手動執行 SQL migration 到 cockswain 資料庫。"
echo "例如（依你現在實際帳號調整）："
echo "  mysql -u cockswain_core -p cockswain < $SQL_FILE"
echo
echo "初始化檔案已建立於：$EVOL_DIR"
