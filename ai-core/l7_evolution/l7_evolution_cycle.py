#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cockswain L7 Evolution Cycle v1.1
---------------------------------
此版本專為母機「SSL 模組殘缺」環境修正：
- mysql.connector 強制 ssl_disabled=True
- 增加 log 輸出（print → systemd journalctl 可看見）
- 增強保護：避免 summary 空檔、避免 JSON decode 中斷
- 全面 UTF-8
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any

import mysql.connector
import yaml

BASE_DIR = Path("/srv/cockswain-core/ai-core")
EVOL_DIR = BASE_DIR / "l7_evolution"
CONFIG_PATH = EVOL_DIR / "config_evolution.yaml"
LOG_DIR = EVOL_DIR / "logs"

NOW = dt.datetime.now()


# -------------------------------------------------------------
# 工具：載入 config
# -------------------------------------------------------------
def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# -------------------------------------------------------------
# 工具：資料庫連線（已關閉 SSL）
# -------------------------------------------------------------
def get_db_conn():
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "cockswain_core")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "cockswain")

    print(f"[L7] Connecting to DB {user}@{host}:{port}/{database} ...")

    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        autocommit=True,
        ssl_disabled=True,  # ★ 關閉 SSL（避免 Python SSL 損壞）
    )


# -------------------------------------------------------------
# 工具：安全讀取 JSONL
# -------------------------------------------------------------
def safe_load_jsonl(path: Path, limit: int) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"[L7] JSONL not found: {path}")
        return []

    items = []
    print(f"[L7] Loading JSONL: {path}")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
                if len(items) >= limit:
                    break
            except Exception:
                # 不中斷，只跳過壞行
                continue
    return items


# -------------------------------------------------------------
# 工具：計算重要性
# -------------------------------------------------------------
def compute_importance(item: Dict[str, Any]) -> float:
    if "importance" in item:
        return float(item.get("importance", 0.5))

    if "priority" in item:
        try:
            p = int(item["priority"])
            return max(0.1, min(1.0, (6 - p) / 5))
        except Exception:
            return 0.5

    return 0.5


# -------------------------------------------------------------
# 寫入：系統狀態
# -------------------------------------------------------------
def record_system_status(conn, cfg: dict):
    cursor = conn.cursor()
    sql = """
    INSERT INTO l7_system_status (
      created_at, overall_health,
      l1_status, l2_status, l3_status, l4_status, l5_status, l6_status, l7_status,
      metrics, notes
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    l_status = {
        "l1": "ready",
        "l2": "pending",
        "l3": "pending",
        "l4": "pending",
        "l5": "partial",
        "l6": "partial",
        "l7": "active",
    }

    metrics = {
        "source": "l7_evolution_v1.1",
        "comment": "placeholder version; will upgrade later",
    }

    cursor.execute(
        sql,
        (
            NOW,
            "good",
            l_status["l1"],
            l_status["l2"],
            l_status["l3"],
            l_status["l4"],
            l_status["l5"],
            l_status["l6"],
            l_status["l7"],
            json.dumps(metrics, ensure_ascii=False),
            "v1.1 自動快照（之後接真正健康狀態）",
        ),
    )
    cursor.close()
    print("[L7] ✔ System status recorded.")


# -------------------------------------------------------------
# 寫入：進化日誌
# -------------------------------------------------------------
def insert_evolution_log(conn, category: str, title: str, summary: str, details=None):
    cursor = conn.cursor()
    sql = """
    INSERT INTO l7_evolution_log (created_at, category, title, summary, details)
    VALUES (%s,%s,%s,%s,%s)
    """
    cursor.execute(
        sql,
        (
            NOW,
            category,
            title,
            summary,
            json.dumps(details, ensure_ascii=False) if details else None,
        ),
    )
    cursor.close()
    print(f"[L7] ✔ Log: {category} - {title}")


# -------------------------------------------------------------
# 寫入：建議任務
# -------------------------------------------------------------
def insert_suggested_task(conn, title: str, description: str, priority: int, meta: Dict[str, Any]):
    cursor = conn.cursor()
    sql = """
    INSERT INTO l7_suggested_tasks (
      created_at, title, description, priority, status, source, meta
    ) VALUES (%s,%s,%s,%s,'suggested','l7_evolution',%s)
    """

    cursor.execute(
        sql,
        (
            NOW,
            title,
            description,
            priority,
            json.dumps(meta, ensure_ascii=False),
        ),
    )
    cursor.close()
    print(f"[L7] ✔ Suggested task created: {title}")


def count_today_suggested_tasks(conn) -> int:
    cursor = conn.cursor()
    sql = """SELECT COUNT(*) FROM l7_suggested_tasks WHERE DATE(created_at)=CURDATE()"""
    cursor.execute(sql)
    (count,) = cursor.fetchone()
    cursor.close()
    return count


# -------------------------------------------------------------
# 核心：認知循環
# -------------------------------------------------------------
def run_cognitive_loop(conn, cfg: dict):
    max_items = int(cfg["cognitive_loop"]["max_items_per_cycle"])
    min_importance = float(cfg["cognitive_loop"]["min_importance_score"])
    max_suggest = int(cfg["self_initiating"]["max_suggested_tasks_per_day"])
    default_priority = int(cfg["self_initiating"]["default_priority"])

    dialog_items = safe_load_jsonl(Path(cfg["sources"]["dialog_summary_path"]), max_items)
    task_items = safe_load_jsonl(Path(cfg["sources"]["task_summary_path"]), max_items)

    all_items = []
    for src, items in (("dialog", dialog_items), ("task", task_items)):
        for it in items:
            it["_src"] = src
            all_items.append(it)

    important_items = [it for it in all_items if compute_importance(it) >= min_importance]

    insert_evolution_log(
        conn,
        "observation",
        "本輪認知循環",
        f"掃描 {len(all_items)} 項，其中 {len(important_items)} 項被判定為重要。",
        {"timestamp": NOW.isoformat()},
    )

    # 建議任務（有每日上限）
    existing = count_today_suggested_tasks(conn)
    remain = max(0, max_suggest - existing)
    if remain <= 0:
        print("[L7] 今日建議任務已達上限。")
        return

    important_items.sort(key=lambda it: compute_importance(it), reverse=True)
    selected = important_items[:remain]

    for it in selected:
        title = it.get("title") or f"{it.get('_src','item')}_task"
        desc = it.get("summary") or it.get("description") or json.dumps(it, ensure_ascii=False)[:500]
        meta = {"source_type": it.get("_src"), "raw": it}
        insert_suggested_task(conn, title, desc, default_priority, meta)

    if selected:
        insert_evolution_log(
            conn,
            "adjustment",
            "已產生建議任務",
            f"本輪共新增 {len(selected)} 項建議任務。",
            {"timestamp": NOW.isoformat()},
        )


# -------------------------------------------------------------
# 寫每日摘要
# -------------------------------------------------------------
def write_daily_evolution_summary(conn):
    summary = (
        "舵手已完成今日的自我檢視，記錄狀態、掃描事件、產生建議任務。"
        "（此為 v1.1 自動摘要，之後可升級為 L7 自主生成版本。）"
    )
    insert_evolution_log(
        conn,
        "daily_summary",
        "舵手每日進化摘要",
        summary,
        {"timestamp": NOW.isoformat()},
    )


# -------------------------------------------------------------
# 主程序
# -------------------------------------------------------------
def ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("[L7] ===== Cockswain L7 Evolution Cycle v1.1 Start =====")

    ensure_log_dir()
    cfg = load_config()

    try:
        conn = get_db_conn()
    except Exception as e:
        print(f"[L7] ❌ DB 連線失敗：{e}")
        return

    try:
        record_system_status(conn, cfg)
        run_cognitive_loop(conn, cfg)
        write_daily_evolution_summary(conn)
    except Exception as e:
        print(f"[L7] ❌ 進化例程錯誤：{e}")
    finally:
        conn.close()

    print("[L7] ===== Evolution Cycle Completed =====")


if __name__ == "__main__":
    main()
