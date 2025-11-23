#!/usr/bin/env python3
import os, json, datetime, sys
LOG_FILE = "/srv/cockswain-core/logs/import_repo_to_db.log"
REPO_ROOT = "/srv/cockswain-core/data/repo"
ENV_PATH = "/srv/cockswain-core/.env"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")
# read .env
env = {}
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

DB_HOST = env.get("MYSQL_HOST", "localhost")
DB_USER = env.get("MYSQL_USER", "root")
DB_PASS = env.get("MYSQL_PASSWORD", "")
DB_NAME = env.get("MYSQL_DATABASE", "cockswain")

try:
    import mysql.connector
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.database = DB_NAME
    cur.execute("""
    CREATE TABLE IF NOT EXISTS records (
      id INT AUTO_INCREMENT PRIMARY KEY,
      trace_id VARCHAR(255),
      topic VARCHAR(255),
      title TEXT,
      description TEXT,
      tags JSON,
      meta JSON,
      content JSON,
      received_at DATETIME NULL,
      inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    log("✅ MySQL connected and table ensured.")
except Exception as e:
    log(f"❌ MySQL connection failed: {e}")
    sys.exit(1)
for root, dirs, files in os.walk(REPO_ROOT):
    for name in files:
        if not name.endswith(".json"):
            continue
        fullpath = os.path.join(root, name)
        try:
            with open(fullpath, encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            summary = data.get("summary", {})
            tags = data.get("tags", [])
            content = data.get("content", {})

            received_at = meta.get("received_at")
            if received_at:
                try:
                    received_at = datetime.datetime.fromisoformat(received_at.replace("Z", "+00:00"))
                except Exception:
                    received_at = None

            cur.execute("""
                INSERT INTO records
                (trace_id, topic, title, description, tags, meta, content, received_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                meta.get("trace_id"),
                meta.get("topic"),
                summary.get("title"),
                summary.get("description"),
                json.dumps(tags, ensure_ascii=False),
                json.dumps(meta, ensure_ascii=False),
                json.dumps(content, ensure_ascii=False),
                received_at
            ))
            conn.commit()
            log(f"✅ Imported: {fullpath}")
        except Exception as e:
            log(f"❌ Error importing {fullpath}: {e}")

cur.close()
conn.close()
log("---- Import completed ----")
