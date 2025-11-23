#!/usr/bin/env python3
import os
import time
import logging
import json
from typing import Any, Dict, Optional

import mysql.connector
import requests

# =========================
# 基本設定
# =========================
LOG_LEVEL = os.getenv("COCKSWAIN_LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [core-bridge] %(levelname)s: %(message)s",
)

logger = logging.getLogger("core-bridge")

# =========================
# DB 連線設定（可被環境變數覆寫）
# =========================
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "cockswain_core")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "change_me")
MYSQL_DB = os.getenv("MYSQL_DB", "cockswain")

# 你原本檔裡就有的這行，保留
MYSQL_SOCKET = os.getenv("MYSQL_SOCKET", "/var/run/mysqld/mysqld.sock")

# =========================
# Orchestrator 設定
# =========================
ORCH_URL = os.getenv("ORCH_URL", "http://127.0.0.1:7780/orchestrate")
ORCH_TIMEOUT = int(os.getenv("ORCH_TIMEOUT", "5"))

# 每幾秒再試一次 DB / 任務
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "3"))


def get_db_conn():
    """
    建立一個禁用 SSL 的 MySQL 連線。
    這是這版最重要的改動：ssl_disabled=True
    """
    # 主連線：走 host/port
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT,
            ssl_disabled=True,  # ← 關鍵：不要用 python 那顆還在 dummy 的 ssl
        )
        return conn
    except mysql.connector.Error as e:
        logger.error(f"db connect error (host/port): {e}")
        # 如果有 socket 再試一次（有些人習慣本機走 socket）
        try:
            conn = mysql.connector.connect(
                unix_socket=MYSQL_SOCKET,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                ssl_disabled=True,  # ← 這裡也要關
            )
            return conn
        except mysql.connector.Error as e2:
            logger.error(f"db connect error (socket): {e2}")
            raise


def fetch_pending_tasks(conn) -> list[Dict[str, Any]]:
    """
    這裡先做成最簡單的：去資料庫拉待處理的任務。
    你可以之後換成你真正的 tasks table / view。
    """
    tasks: list[Dict[str, Any]] = []
    try:
        cursor = conn.cursor(dictionary=True)
        # 這裡用一個保守的假表格名，之後你換成真正的
        cursor.execute(
            "SELECT id, payload FROM tasks WHERE status='pending' ORDER BY created_at ASC LIMIT 10"
        )
        for row in cursor.fetchall():
            tasks.append(row)
        cursor.close()
    except mysql.connector.Error as e:
        logger.error(f"db query error: {e}")
    return tasks


def call_orchestrator(task: Dict[str, Any]) -> bool:
    """
    呼叫本機的 orchestrator，把任務丟過去。
    你之前的 log 有出現：call_orchestrator error: timed out
    我這裡也保留這個錯誤格式，方便對 log。
    """
    try:
        resp = requests.post(
            ORCH_URL,
            json=task,
            timeout=ORCH_TIMEOUT,
        )
        if resp.status_code == 200:
            return True
        else:
            logger.error(f"call_orchestrator error: http {resp.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.error("call_orchestrator error: timed out")
        return False
    except Exception as e:
        logger.error(f"call_orchestrator error: {e}")
        return False


def mark_task_done(conn, task_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET status='done', updated_at=NOW() WHERE id=%s",
            (task_id,),
        )
        conn.commit()
        cursor.close()
    except mysql.connector.Error as e:
        logger.error(f"db update error: {e}")


def main_loop():
    logger.info("core_bridge started.")
    conn: Optional[mysql.connector.connection.MySQLConnection] = None

    while True:
        # 確保手上有 DB 連線
        if conn is None or not conn.is_connected():
            try:
                conn = get_db_conn()
            except Exception:
                # 上面已經 log 過了
                time.sleep(POLL_INTERVAL)
                continue

        # 拉任務
        tasks = fetch_pending_tasks(conn)
        if tasks:
            logger.info(f"fetched {len(tasks)} pending tasks")
        else:
            # 沒事就睡一下
            time.sleep(POLL_INTERVAL)
            continue

        # 一個一個處理
        for t in tasks:
            task_id = t.get("id")
            payload = t.get("payload")
            # payload 若是字串就轉 dict
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    # 就用原始的
                    pass

            ok = call_orchestrator({"id": task_id, "payload": payload})
            if ok and task_id is not None:
                mark_task_done(conn, task_id)

        # 不要炸 CPU
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("core_bridge stopped.")
