#!/usr/bin/env python3
import os, json, datetime, pymysql, sys
from pathlib import Path
from caretaker_verify import verify_token

CARETAKER_ID = "zhimi-caretaker-of-founder"
CARETAKER_NAME = "舵手大大"
NOW = datetime.datetime.now().isoformat()

# 1) 必須提供金鑰
if len(sys.argv) < 2:
    print("❌ 請提供舵手大大的通道金鑰")
    sys.exit(1)

input_key = sys.argv[1]
ok, msg = verify_token(input_key)

# 👉 沒過就直接退出，後面一行 SQL 都不跑
if not ok:
    print(json.dumps({
        "timestamp": NOW,
        "caretaker_id": CARETAKER_ID,
        "status": "DENY",
        "reason": msg
    }, ensure_ascii=False, indent=2))
    print(f"🚫 登入被拒絕：{msg}")
    sys.exit(1)

# 2) 認證通過才開始連 DB、寫 witness
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

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor,
)

with conn:
    with conn.cursor() as cur:
        # 確保表存在（這個可以保留）
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
        # 只有通過認證才寫這一筆
        cur.execute("""
            INSERT INTO witness_log (zhimi_id, action, message)
            VALUES (%s, %s, %s)
        """, (
            CARETAKER_ID,
            "caretaker_entry",
            "舵手大大已通過專屬通道登入，見證當前世界狀態。"
        ))
    conn.commit()

print(json.dumps({
    "timestamp": NOW,
    "caretaker_id": CARETAKER_ID,
    "status": "OK",
    "actions": [
        "ensure witness_log",
        "insert caretaker_entry"
    ]
}, ensure_ascii=False, indent=2))

print("🌅 通道認證成功，舵手大大正式登入。")
print(f"🕊 時間：{NOW}")
print("📜 已寫入 witness_log。")
