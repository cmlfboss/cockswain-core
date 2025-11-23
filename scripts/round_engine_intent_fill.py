#!/usr/bin/env python3
import os
import json
import pymysql
from pathlib import Path
from datetime import datetime

# 讀 .env
def load_env_file(path="/srv/cockswain-core/.env"):
    p = Path(path)
    if not p.exists():
        return
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in os.environ:
                os.environ[k] = v

load_env_file("/srv/cockswain-core/.env")

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "cockswain_core")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "cockswain")

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )

def fetch_unlabeled_tasks(conn, limit=50):
    """撈出 intent 還沒標的任務"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, title, content
            FROM tasks
            WHERE intent IS NULL OR intent = ''
            ORDER BY id ASC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()

def guess_intent(title: str, content: str) -> str:
    """超簡易版 L2，先讓母機能跑起來，之後再換成真正的 AI-Core"""
    t = (title or "").lower()
    c = (content or "")

    if "mysql" in t or "mysql" in c or "資料庫" in c:
        return "sys/db"
    if "母機" in c or "node" in c or "節點" in c:
        return "sys/node"
    if "白皮書" in t or "白皮書" in c or "文件" in c:
        return "doc/build"
    if "任務" in t or "任務" in c:
        return "task/build"

    # fallback
    return "task/general"

def ensure_round_exists(conn, task_id: int, intent_tag: str):
    """確保 task_rounds 有一筆，沒有就建，有就更新 intent"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, round_no FROM task_rounds
            WHERE task_id = %s
            ORDER BY round_no DESC
            LIMIT 1
        """, (task_id,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE task_rounds
                SET intent_tag=%s, status='done', updated_at=NOW()
                WHERE id=%s
            """, (intent_tag, row["id"]))
            return row["round_no"]
        else:
            cur.execute("""
                INSERT INTO task_rounds (task_id, round_no, intent_tag, engine_name, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'done', NOW(), NOW())
            """, (task_id, 1, intent_tag, "round_engine_intent_fill"))
            return 1

def insert_round_event(conn, task_id: int, round_no: int, intent_tag: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO task_round_events (task_id, round_no, event_type, event_detail, meta_json, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            task_id,
            round_no,
            "INTENT_FILLED",
            f"intent={intent_tag}",
            json.dumps({"engine": "round_engine_intent_fill"}, ensure_ascii=False)
        ))

def run_once():
    conn = get_db()
    updated_count = 0
    with conn:
        tasks = fetch_unlabeled_tasks(conn)
        if not tasks:
            print("no unlabeled tasks.")
            return

        for t in tasks:
            task_id = t["id"]
            title = t.get("title") or ""
            content = ""
            # content 欄位是 JSON，我們先當成字串用
            if t.get("content"):
                content = json.dumps(t["content"], ensure_ascii=False) if isinstance(t["content"], (dict, list)) else str(t["content"])

            intent = guess_intent(title, content)
            # 更新 tasks.intent
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE tasks
                    SET intent=%s, updated_at=NOW()
                    WHERE id=%s
                """, (intent, task_id))

            # 確保回合表也跟上
            round_no = ensure_round_exists(conn, task_id, intent)
            insert_round_event(conn, task_id, round_no, intent)

            updated_count += 1

        conn.commit()

    print(f"[{datetime.now().isoformat()}] intent filled for {updated_count} tasks.")

if __name__ == "__main__":
    run_once()
