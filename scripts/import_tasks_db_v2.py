#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import shutil
import datetime
from pathlib import Path
import mysql.connector
import importlib
import sys

BASE = Path("/srv/cockswain-core")
PROCESSED = BASE / "tasks" / "processed"
ARCHIVE = BASE / "tasks" / "archived"
LOG = BASE / "logs" / "import-tasks.log"
ENV_FILE = BASE / ".env"

ARCHIVE.mkdir(parents=True, exist_ok=True)
LOG.parent.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    ts = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

def load_env(path: Path):
    env = {}
    if not path.exists():
        log(f"⚠️ 未找到 {path}，改用預設連線參數")
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def get_db_connection(env):
    try:
        conn = mysql.connector.connect(
            host=env.get("MYSQL_HOST", "localhost"),
            port=int(env.get("MYSQL_PORT", 3306)),
            user=env.get("MYSQL_USER", "cockswain_core"),
            password=env.get("MYSQL_PASSWORD", ""),
            database=env.get("MYSQL_DATABASE", "cockswain"),
            ssl_disabled=True,
        )
        return conn
    except mysql.connector.Error as e:
        log(f"❌ 資料庫連線失敗: {e}")
        return None

def run_l1_pipeline(payload: dict):
    try:
        ai_core_path = BASE / "ai-core"
        pipelines_path = ai_core_path / "pipelines"
        sys.path.insert(0, str(ai_core_path))
        sys.path.insert(0, str(pipelines_path))
        l1_mod = importlib.import_module("pipelines.l1_intent")
        out = l1_mod.process({"text": payload.get("text", "")}, {})
        return out.get("l1_intent", "unknown"), out.get("l1_intent_detail", "unknown")
    except Exception as e:
        log(f"⚠️ L1 pipeline 執行失敗：{e}")
        return "unknown", "unknown"

def insert_task_ingest(conn, data: dict, raw_json: str, intent: str, intent_detail: str, filename: str):
    title = data.get("title", "未命名任務")
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO task_ingest (title, raw_json, intent, intent_detail, src_filename, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, raw_json, intent, intent_detail, filename, created_at))
    conn.commit()
    cur.close()
    log(f"✅ 已寫入 task_ingest：{title} ({intent}/{intent_detail})")

def insert_tasks_fallback(conn, data: dict, raw_json: str):
    title = data.get("title", "未命名任務")
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, content, created_at)
        VALUES (%s, %s, %s)
    """, (title, raw_json, created_at))
    conn.commit()
    cur.close()
    log(f"✅ fallback → 已寫入 tasks：{title}")

def process_file(conn, file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_json = json.dumps(data, ensure_ascii=False)

    intent, intent_detail = run_l1_pipeline(data)

    try:
        insert_task_ingest(conn, data, raw_json, intent, intent_detail, file_path.name)
    except Exception as e:
        log(f"⚠️ 寫入 task_ingest 失敗，改用 tasks：{e}")
        insert_tasks_fallback(conn, data, raw_json)

    archived = ARCHIVE / file_path.name
    shutil.move(str(file_path), str(archived))
    log(f"📦 已封存：{archived}")

def main():
    env = load_env(ENV_FILE)
    conn = get_db_connection(env)
    if not conn:
        log("❌ 無法連線資料庫，結束。")
        return

    files = sorted(PROCESSED.glob("*.json"))
    if not files:
        log("ℹ️ 沒有任務檔可匯入。")
        conn.close()
        return

    log(f"🔍 找到 {len(files)} 個任務檔，開始匯入 (v2)...")
    for fp in files:
        process_file(conn, fp)

    conn.close()
    log("🎯 任務匯入 v2 流程完成。")

if __name__ == "__main__":
    main()
