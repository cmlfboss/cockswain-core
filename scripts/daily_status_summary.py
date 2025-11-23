#!/usr/bin/env python3
import os
import json
import datetime
import pymysql
from pathlib import Path

# 讀 .env
def load_env(path="/srv/cockswain-core/.env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k not in os.environ:
            os.environ[k] = v

load_env()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "cockswain_core")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "cockswain")

NOW = datetime.datetime.now()

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )

def get_latest_selfcheck(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, run_at, status, checks_text, advice_text
            FROM task_import_selfcheck_logs
            ORDER BY id DESC
            LIMIT 1
        """)
        return cur.fetchone()

def count_tasks_today(conn):
    today = NOW.date()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS c
            FROM tasks
            WHERE DATE(created_at) = %s
        """, (today,))
        row = cur.fetchone()
        return row["c"] if row else 0

def count_unlabeled(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS c
            FROM tasks
            WHERE intent IS NULL OR intent = ''
        """)
        row = cur.fetchone()
        return row["c"] if row else 0

def main():
    report = {
        "timestamp": NOW.isoformat(),
        "status": "OK",
        "selfcheck": {},
        "metrics": {},
        "advice": []
    }

    conn = get_db()
    with conn:
        # 最新自檢結果
        latest = get_latest_selfcheck(conn)
        if latest:
            report["selfcheck"] = {
                "run_at": latest["run_at"].isoformat(),
                "status": latest["status"],
            }
            if latest["status"] != "OK":
                report["status"] = "WARN"
                report["advice"].append("最新自檢狀態不是 OK，請查看 task_import_selfcheck_logs。")
        else:
            report["status"] = "WARN"
            report["advice"].append("尚未有自檢紀錄。")

        # 今日任務數
        tasks_today = count_tasks_today(conn)
        report["metrics"]["tasks_today"] = tasks_today

        # 尚未標意圖的數量
        unlabeled = count_unlabeled(conn)
        report["metrics"]["unlabeled_tasks"] = unlabeled
        if unlabeled > 0:
            report["status"] = "WARN"
            report["advice"].append(f"仍有 {unlabeled} 筆任務未標記 intent，等待 intentfill timer 處理。")

        # 寫入彙整表
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO daily_status_summary (run_at, status, payload_json)
                    VALUES (NOW(), %s, %s)
                """, (
                    report["status"],
                    json.dumps(report, ensure_ascii=False),
                ))
            conn.commit()
        except Exception as e:
            # 表還沒建也沒關係，先照樣印
            report["advice"].append(f"summary write failed: {repr(e)}")

    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
