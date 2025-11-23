#!/usr/bin/env python3
import mysql.connector
from pathlib import Path
import json

BASE = Path("/srv/cockswain-core")
ENV_FILE = BASE / ".env"

def load_env(path: Path):
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def main():
    env = load_env(ENV_FILE)
    conn = mysql.connector.connect(
        host=env.get("DB_HOST", "127.0.0.1"),
        port=int(env.get("DB_PORT", "3306")),
        database=env.get("DB_NAME", "cockswain"),
        user=env.get("DB_USER", "cockswain_core"),
        password=env.get("DB_PASS", ""),
        ssl_disabled=True,
    )
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, src_filename, agent_name, intent, src, ts_raw, created_at
        FROM task_ingest
        ORDER BY id DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("no tasks found.")
        return

    for r in rows:
        print(f"[{r['id']}] {r['agent_name']}  {r['intent'] or '-'}  {r['src_filename']}  {r['created_at']}")
        if r.get("ts_raw"):
            print(f"   ts: {r['ts_raw']}")
        if r.get("src"):
            print(f"   src: {r['src']}")
    print("-- end --")

if __name__ == "__main__":
    main()
