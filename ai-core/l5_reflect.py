#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
l5_reflect.py
Cockswain L5 Self-Reflection Worker

用途：
- 週期性掃描 task_runs 表，找出「還沒被統計過」的執行紀錄
- 依照 agent / backend 分別累加成功次數、失敗次數
- 失敗時記錄 last_error，讓仲裁器可以之後參考
- 把「我掃到哪一筆了」記在本機檔案，避免每次都從頭掃

這支程式只讀寫本地 MySQL，不對外，是純後台 worker。
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

import mysql.connector

# ====== MySQL 設定（跟你現有服務一樣）======
MYSQL_DB = "cockswain"
MYSQL_USER = "cockswain_core"
MYSQL_PASSWORD = "cSWN!_2025-m0ther-N0de#1"
MYSQL_SOCKET = "/var/run/mysqld/mysqld.sock"

# ====== 設定 ======
STATE_DIR = Path("/srv/cockswain-core/state")
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "l5_reflect_state.json"

POLL_INTERVAL = 5  # 幾秒掃一次
BATCH_SIZE = 50    # 一次吃多少筆 task_runs


def get_db():
    return mysql.connector.connect(
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        unix_socket=MYSQL_SOCKET,
        ssl_disabled=True,
    )


def load_state() -> int:
    """讀取我們上次掃到哪一筆 task_runs.id 了"""
    if not STATE_FILE.exists():
        return 0
    try:
        data = json.loads(STATE_FILE.read_text())
        return int(data.get("last_task_run_id", 0))
    except Exception:
        return 0


def save_state(last_id: int):
    STATE_FILE.write_text(json.dumps({"last_task_run_id": last_id}))


def fetch_new_runs(since_id: int):
    """抓還沒處理過的 task_runs"""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT id, task_id, agent, backend, status, result_text, started_at, ended_at
        FROM task_runs
        WHERE id > %s
        ORDER BY id ASC
        LIMIT %s
        """,
        (since_id, BATCH_SIZE),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def upsert_agent_stat(agent: str, status: str, last_error: str | None, last_run_at: datetime | None):
    conn = get_db()
    cur = conn.cursor()
    # 先確保有一列
    cur.execute(
        "SELECT id, total_runs, success_runs, failed_runs FROM agent_stats WHERE agent=%s",
        (agent,),
    )
    row = cur.fetchone()
    now = datetime.utcnow()

    if row is None:
        # 新增
        total_runs = 1
        success_runs = 1 if status == "done" else 0
        failed_runs = 1 if status != "done" else 0
        cur.execute(
            """
            INSERT INTO agent_stats
              (agent, total_runs, success_runs, failed_runs, last_error, last_run_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (agent, total_runs, success_runs, failed_runs, last_error, last_run_at, now),
        )
    else:
        # 更新
        _id, total_runs, success_runs, failed_runs = row
        total_runs += 1
        if status == "done":
            success_runs += 1
        else:
            failed_runs += 1
        cur.execute(
            """
            UPDATE agent_stats
            SET total_runs=%s,
                success_runs=%s,
                failed_runs=%s,
                last_error=%s,
                last_run_at=%s,
                updated_at=%s
            WHERE agent=%s
            """,
            (
                total_runs,
                success_runs,
                failed_runs,
                last_error,
                last_run_at,
                now,
                agent,
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


def upsert_backend_stat(backend: str, status: str, last_error: str | None, last_run_at: datetime | None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, total_runs, success_runs, failed_runs FROM backend_stats WHERE backend=%s",
        (backend,),
    )
    row = cur.fetchone()
    now = datetime.utcnow()

    if row is None:
        total_runs = 1
        success_runs = 1 if status == "done" else 0
        failed_runs = 1 if status != "done" else 0
        cur.execute(
            """
            INSERT INTO backend_stats
              (backend, total_runs, success_runs, failed_runs, last_error, last_run_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (backend, total_runs, success_runs, failed_runs, last_error, last_run_at, now),
        )
    else:
        _id, total_runs, success_runs, failed_runs = row
        total_runs += 1
        if status == "done":
            success_runs += 1
        else:
            failed_runs += 1
        cur.execute(
            """
            UPDATE backend_stats
            SET total_runs=%s,
                success_runs=%s,
                failed_runs=%s,
                last_error=%s,
                last_run_at=%s,
                updated_at=%s
            WHERE backend=%s
            """,
            (
                total_runs,
                success_runs,
                failed_runs,
                last_error,
                last_run_at,
                now,
                backend,
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


def main_loop():
    last_id = load_state()
    print(f"[l5] start reflect loop from task_run_id > {last_id}")

    while True:
        rows = fetch_new_runs(last_id)
        if not rows:
            time.sleep(POLL_INTERVAL)
            continue

        for row in rows:
            rid = row["id"]
            agent = row.get("agent") or "default"
            backend = row.get("backend") or "unknown"
            status = row.get("status") or "unknown"
            result_text = row.get("result_text") or ""
            started_at = row.get("started_at") or datetime.utcnow()

            last_error = None
            if status != "done":
                # 失敗的話抓一點錯誤字串進來
                last_error = result_text[:200]

            # 更新 agent 統計
            upsert_agent_stat(agent, status, last_error, started_at)
            # 更新 backend 統計
            upsert_backend_stat(backend, status, last_error, started_at)

            # 更新我們掃描的位置
            last_id = rid
            save_state(last_id)

        # 下一輪
        time.sleep(1)


if __name__ == "__main__":
    main_loop()
