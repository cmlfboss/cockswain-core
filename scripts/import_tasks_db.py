#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cockswain Task Importer v1.3
- 從 /tasks/processed 讀 JSON
- 寫進 MySQL
- 成功的搬到 /tasks/archived
- 關閉 MySQL SSL，避免環境沒 ssl.wrap_socket 的錯
"""

import os
import json
import shutil
import datetime
from pathlib import Path
import mysql.connector

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
        log(f"⚠️ 未找到 {path}，將使用預設連線參數")
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
    host = env.get("MYSQL_HOST", "localhost")
    port = int(env.get("MYSQL_PORT", 3306))
    user = env.get("MYSQL_USER", "cockswain_core")
    password = env.get("MYSQL_PASSWORD", "")
    database = env.get("MYSQL_DATABASE", "cockswain")

    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl_disabled=True,  # 👈 關掉 SSL，避免 ssl.wrap_socket 錯
        )
        return conn
    except mysql.connector.Error as e:
        log(f"❌ 資料庫連線失敗: {e}")
        return None

def import_task_file(conn, file_path: Path):
    # 這裡先用最通用的欄位：title + content
    # 之後你要改成 task_ingest 的欄位我們再調
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("title", file_path.stem)
        content = json.dumps(data, ensure_ascii=False)
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.cursor()
        # 先寫進 tasks，若你只建立了 task_ingest 就把這段換掉
        cur.execute("""
            INSERT INTO tasks (title, content, created_at)
            VALUES (%s, %s, %s)
        """, (title, content, created_at))
        conn.commit()
        cur.close()

        log(f"✅ 匯入成功：{file_path.name}")
        return True
    except Exception as e:
        log(f"❌ 匯入失敗：{file_path.name}，原因：{e}")
        return False

def main():
    env = load_env(ENV_FILE)
    conn = get_db_connection(env)
    if not conn:
        log("❌ 無法連線資料庫，程序結束。")
        return

    files = sorted(PROCESSED.glob("*.json"))
    if not files:
        log("ℹ️ 沒有任務檔可匯入。")
        conn.close()
        return

    log(f"🔍 找到 {len(files)} 個任務檔，開始匯入...")
    for fp in files:
        ok = import_task_file(conn, fp)
        if ok:
            archived_path = ARCHIVE / fp.name
            shutil.move(str(fp), str(archived_path))
            log(f"📦 已封存：{archived_path}")

    conn.close()
    log("🎯 匯入作業完成。")

if __name__ == "__main__":
    main()
