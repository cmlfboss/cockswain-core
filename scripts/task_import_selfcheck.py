#!/usr/bin/env python3
import os
import json
import datetime
import pymysql
from pathlib import Path

# 讀 .env
def load_env_file(path="/srv/cockswain-core/.env"):
    p = Path(path)
    if not p.exists():
        return
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

load_env_file("/srv/cockswain-core/.env")

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


def table_exists(conn, table_name):
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES LIKE %s", (table_name,))
        return cur.fetchone() is not None


def get_columns(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(f"SHOW COLUMNS FROM {table_name}")
        rows = cur.fetchall()
    return [r["Field"] for r in rows]


def count_today(conn, table_name, ts_col):
    today = NOW.date()
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS c FROM {table_name} WHERE DATE({ts_col})=%s",
            (today,),
        )
        row = cur.fetchone()
        return row["c"] if row else 0


def fetch_recent_tasks(conn, limit=20):
    """根據實際欄位組查詢，不會撈不存在的欄位"""
    cols = get_columns(conn, "tasks")

    select_cols = ["id"]
    for c in ["title", "content", "status", "intent", "updated_at", "created_at"]:
        if c in cols:
            select_cols.append(c)

    col_sql = ", ".join(select_cols)

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {col_sql} FROM tasks ORDER BY id DESC LIMIT %s", (limit,)
        )
        rows = cur.fetchall()
    return rows, cols


def count_fallback(conn, cols, limit_days=1):
    """只有在有 intent + updated_at 時才檢查 fallback"""
    if "intent" not in cols or "updated_at" not in cols:
        return None

    date_from = (NOW - datetime.timedelta(days=limit_days)).date()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS c
            FROM tasks
            WHERE intent='fallback'
              AND DATE(updated_at) >= %s
            """,
            (date_from,),
        )
        row = cur.fetchone()
    return row["c"] if row else 0


def main():
    report = {
        "timestamp": NOW.isoformat(),
        "status": "OK",
        "checks": [],
        "advice": [],
    }

    # 連 DB
    try:
        conn = get_db()
    except Exception as e:
        report["status"] = "ERROR"
        report["checks"].append(
            {
                "name": "db_connection",
                "result": "fail",
                "detail": str(e),
            }
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    with conn:
        # 1) 檢查必要表
        needed = [
            "tasks",
            "task_ingest",
            "task_rounds",
            "task_round_events",
        ]
        for t in needed:
            exists = table_exists(conn, t)
            report["checks"].append(
                {
                    "name": f"table_{t}",
                    "result": "ok" if exists else "missing",
                }
            )
            if not exists:
                report["status"] = "WARN"
                report["advice"].append(
                    f"資料表 {t} 不存在，請確認該階段流程是否已部署。"
                )

        # 2) 有 tasks 才做後面的檢查
        if table_exists(conn, "tasks"):
            cols = get_columns(conn, "tasks")

            # 2a) 今天有沒有任務
            ts_col = None
            if "created_at" in cols:
                ts_col = "created_at"
            elif "updated_at" in cols:
                ts_col = "updated_at"

            if ts_col:
                today_cnt = count_today(conn, "tasks", ts_col)
                report["checks"].append(
                    {
                        "name": "today_tasks",
                        "result": "ok",
                        "value": today_cnt,
                    }
                )
                if today_cnt == 0:
                    report["status"] = "WARN"
                    report["advice"].append(
                        "今天沒有新的 tasks，請確認 import_tasks_db_v2.py 是否有執行。"
                    )
            else:
                report["checks"].append(
                    {
                        "name": "today_tasks",
                        "result": "skipped",
                        "detail": "tasks 表沒有 created_at / updated_at 欄位",
                    }
                )

            # 2b) 最近任務的 intent 狀況
            recent, cols = fetch_recent_tasks(conn)
            if "intent" in cols:
                missing_intent = [r for r in recent if not r.get("intent")]
                report["checks"].append(
                    {
                        "name": "recent_tasks_intent",
                        "result": "ok" if not missing_intent else "partial",
                        "missing_count": len(missing_intent),
                    }
                )
                if missing_intent:
                    report["status"] = "WARN"
                    report["advice"].append(
                        f"最近有 {len(missing_intent)} 筆任務沒有意圖標記，建議啟動 L2 常識判斷補標。"
                    )
            else:
                report["checks"].append(
                    {
                        "name": "recent_tasks_intent",
                        "result": "skipped",
                        "detail": "tasks 表沒有 intent 欄位",
                    }
                )

            # 2c) fallback 數量
            fb_cnt = count_fallback(conn, cols, 1)
            if fb_cnt is None:
                report["checks"].append(
                    {
                        "name": "fallback_daily",
                        "result": "skipped",
                        "detail": "tasks 表沒有 intent / updated_at 欄位",
                    }
                )
            else:
                report["checks"].append(
                    {
                        "name": "fallback_daily",
                        "result": "ok" if fb_cnt < 5 else "high",
                        "value": fb_cnt,
                    }
                )
                if fb_cnt >= 5:
                    report["status"] = "WARN"
                    report["advice"].append(
                        "fallback 次數偏高，建議開始串接 L2 常識判斷。"
                    )

    # 寫入資料庫的自檢日誌（重新開一條連線，避免前面 with conn: 已經關掉）
    try:
        log_conn = get_db()
        with log_conn:
            with log_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO task_import_selfcheck_logs (status, checks_text, advice_text)
                    VALUES (%s, %s, %s)
                """, (
                    report["status"],
                    json.dumps(report["checks"], ensure_ascii=False),
                    json.dumps(report["advice"], ensure_ascii=False),
                ))
            log_conn.commit()
    except Exception as e:
        # 如果寫入失敗，就記在報告裡，但不要讓整個自檢失敗
        report["advice"].append(f"selfcheck log write failed (final): {repr(e)}")

    # 不管怎樣都印出來
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
