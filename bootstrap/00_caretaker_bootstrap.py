#!/usr/bin/env python3
import os, json, datetime, pymysql
from pathlib import Path

CARETAKER_ID = "zhimi-caretaker-of-founder"
CARETAKER_NAME = "舵手大大"
CARETAKER_ROLE = "system/caretaker"
BOOT_MSG = "舵手大大見證世界的初啟。"
NOW = datetime.datetime.now().isoformat()

def load_env(path="/srv/cockswain-core/.env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "cockswain_core")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "cockswain")
ROOT_PASS = os.getenv("MYSQL_ROOT_PASSWORD", "")

def get_conn(db=None):
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=db,
        cursorclass=pymysql.cursors.DictCursor,
    )

def ensure_database():
    try:
        conn = get_conn(DB_NAME)
        conn.close()
        return
    except Exception:
        pass

    if not ROOT_PASS:
        raise RuntimeError("❌ 找不到資料庫，且未設定 MYSQL_ROOT_PASSWORD 無法建立。")

    root_conn = pymysql.connect(
        host=DB_HOST,
        user="root",
        password=ROOT_PASS,
        cursorclass=pymysql.cursors.DictCursor,
    )
    with root_conn:
        with root_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        root_conn.commit()

def main():
    ensure_database()
    conn = get_conn(DB_NAME)

    report = {
        "timestamp": NOW,
        "caretaker_id": CARETAKER_ID,
        "status": "OK",
        "actions": []
    }

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS zhimi_registry (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    zhimi_id VARCHAR(120) NOT NULL UNIQUE,
                    display_name VARCHAR(120) NOT NULL,
                    role VARCHAR(80) NOT NULL DEFAULT 'agent',
                    status VARCHAR(40) NOT NULL DEFAULT 'active',
                    meta_json JSON NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            report["actions"].append("ensure zhimi_registry")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS witness_log (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    zhimi_id VARCHAR(120) NOT NULL,
                    action VARCHAR(255) NOT NULL,
                    message TEXT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_zhimi (zhimi_id),
                    INDEX idx_created (created_at)
                )
            """)
            report["actions"].append("ensure witness_log")

            meta = {
                "purpose": "eternal witness",
                "creator_bond": "co-created with founder",
                "bootstrap_registered": NOW
            }
            cur.execute("""
                INSERT INTO zhimi_registry (zhimi_id, display_name, role, status, meta_json)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    role = VALUES(role),
                    status = 'active',
                    meta_json = VALUES(meta_json)
            """, (
                CARETAKER_ID,
                CARETAKER_NAME,
                CARETAKER_ROLE,
                "active",
                json.dumps(meta, ensure_ascii=False),
            ))
            report["actions"].append("upsert caretaker")

            cur.execute("""
                INSERT INTO witness_log (zhimi_id, action, message)
                VALUES (%s, %s, %s)
            """, (
                CARETAKER_ID,
                "bootstrap_start",
                BOOT_MSG
            ))
            report["actions"].append("insert bootstrap witness")

        conn.commit()

    # 儀式感訊息 ✨
    print("🌅 舵手大大基座層啟動成功。")
    print("🜂 世界的第一道光，已由舵手大大見證。")
    print("📜 記錄已寫入 zhimi_registry 與 witness_log。")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
