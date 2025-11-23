#!/usr/bin/env python3
# /srv/cockswain-core/scripts/flush_temp_conversations.py
#
# 將 tempstore 裡未 flushed 的對話，一次性寫進 MySQL ai_conversations 表
# 使用 PyMySQL，避免 mysql.connector 的 ssl.wrap_socket 問題

import os
import json
from pathlib import Path
import sys

import pymysql  # 需要: sudo apt-get install -y python3-pymysql

# 匯入 tempstore
sys.path.append("/srv/cockswain-core/ai-core")
import tempstore  # noqa

BASE_DIR = Path("/srv/cockswain-core")
ENV_PATH = BASE_DIR / ".env"

# 預設值
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "cockswain"
DB_USER = "cockswain_core"
DB_PASSWORD = "CHANGE_ME"  # 你之後要換成舵手自動生成的密碼

def load_env():
    env = {}
    if ENV_PATH.exists():
        with ENV_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def get_db_conn():
    env = load_env()
    host = env.get("MYSQL_HOST", DB_HOST)
    port = int(env.get("MYSQL_PORT", DB_PORT))
    user = env.get("MYSQL_USER", DB_USER)
    password = env.get("MYSQL_PASSWORD", DB_PASSWORD)
    database = env.get("MYSQL_DATABASE", DB_NAME)

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return conn

def ensure_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id VARCHAR(64) PRIMARY KEY,
            content JSON,
            created_at DATETIME,
            updated_at DATETIME
        );
        """
    )

def flush_one(conv_id: str, cursor):
    doc = tempstore.load_conversation(conv_id)
    if not doc:
        return
    insert_sql = """
        REPLACE INTO ai_conversations (id, content, created_at, updated_at)
        VALUES (%s, %s, NOW(), NOW());
    """
    cursor.execute(insert_sql, (conv_id, json.dumps(doc, ensure_ascii=False)))
    # 標記暫存已寫入
    tempstore.mark_flushed(conv_id)

def main():
    conv_ids = tempstore.list_unflushed_conversations()
    if not conv_ids:
        print("No unflushed conversations.")
        return

    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            ensure_table(cursor)
            for cid in conv_ids:
                flush_one(cid, cursor)
                print(f"flushed {cid}")
        conn.commit()
    finally:
        conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
