#!/usr/bin/env python3
import os
import pymysql
import datetime
import json
from pathlib import Path

# 每張表要保留幾天 + 它的時間欄位
RETENTION = {
    "task_import_selfcheck_logs": ("run_at", 30),
    "daily_status_summary": ("run_at", 60),
    "task_round_events": ("created_at", 90),
}

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

now = datetime.datetime.now()
report = {"timestamp": now.isoformat(), "deleted": {}, "status": "OK"}

with conn:
    for table, (ts_col, days) in RETENTION.items():
        cutoff = now - datetime.timedelta(days=days)
        q = f"DELETE FROM {table} WHERE {ts_col} < %s"
        try:
            with conn.cursor() as cur:
                cur.execute(q, (cutoff,))
                deleted = cur.rowcount
            conn.commit()
            report["deleted"][table] = deleted
        except Exception as e:
            report["deleted"][table] = f"error: {repr(e)}"
            report["status"] = "WARN"

print(json.dumps(report, ensure_ascii=False, indent=2))
