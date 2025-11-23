cd /srv/cockswain-core/ai-core

mkdir -p knowledge_center/knowledge-center
cp knowledge_center/knowledge-center/process_inbox.py knowledge_center/knowledge-center/process_inbox.py.bak_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

cat > knowledge_center/knowledge-center/process_inbox.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KC Inbox Processor v0.2 (mirror)
和 ../process_inbox.py 同步邏輯，避免舊路徑被呼叫時出現不一致。
"""

import os
import sys
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List

import mysql.connector

BASE_DIR = Path(__file__).resolve().parent.parent  # /srv/cockswain-core/ai-core/knowledge_center/..
KC_DIR = BASE_DIR / "knowledge_center"

DEFAULT_SOURCE = "openai"
ENV_PATH = Path("/srv/cockswain-core/.env")

INBOX_ROOT = KC_DIR / "inbox"
PROCESSED_ROOT = KC_DIR / "processed"
FAILED_ROOT = KC_DIR / "failed"


def now_ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def log(msg: str) -> None:
    print(f"[{now_ts()}] [kc] {msg}", flush=True)


def load_env(env_path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not env_path.exists():
        log(f"[warn] 找不到 .env: {env_path}")
        return env

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip("'").strip('"')
        env[k.strip()] = v
    return env


def get_db_config(env: Dict[str, str]) -> Dict[str, Any]:
    host = env.get("KC_DB_HOST") or env.get("DB_HOST") or "localhost"
    name = env.get("KC_DB_NAME") or env.get("DB_NAME") or "cockswain"
    user = env.get("KC_DB_USER") or env.get("DB_USER") or "cockswain_core"
    pwd = (
        env.get("KC_DB_PASSWORD")
        or env.get("DB_PASSWORD")
        or env.get("COCKSWAIN_DB_PASSWORD")
        or ""
    )
    return {"host": host, "database": name, "user": user, "password": pwd}


def get_db_connection(cfg: Dict[str, Any]):
    log(
        f"[db] env_path={ENV_PATH}, host={cfg['host']}, "
        f"name={cfg['database']}, user='{cfg['user']}'@'localhost', "
        f"pwd_len={len(cfg['password'])}"
    )
    conn = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        auth_plugin="mysql_native_password",
        ssl_disabled=True,
    )
    conn.autocommit = True
    return conn


def parse_file_to_entries(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0][:200] if lines else path.name
    content = text
    return [{"raw_path": str(path), "title": title, "content": content}]


def build_kc_entries_insert(cursor, entry: Dict[str, Any], source: str) -> (str, List[Any]):
    cursor.execute("SHOW COLUMNS FROM kc_entries")
    cols = cursor.fetchall()
    values: Dict[str, Any] = {}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for field, col_type, nullable, key, default, extra in cols:
        if "auto_increment" in (extra or "").lower():
            continue

        name_l = field.lower()

        if name_l in ("source", "src", "entry_source"):
            values[field] = source
        elif name_l in ("title", "entry_title"):
            values[field] = entry["title"]
        elif name_l in ("content", "body", "entry_content", "text"):
            values[field] = entry["content"]
        elif name_l in ("created_at", "created_ts", "indexed_at", "ts"):
            values[field] = now
        elif "tag" in name_l:
            values[field] = "[]"
        elif "meta" in name_l or "extra" in name_l:
            values[field] = "{}"
        else:
            if default is not None:
                values[field] = None
            elif nullable.upper() == "YES":
                values[field] = None
            else:
                values[field] = "N/A"

    insert_cols = list(values.keys())
    placeholders = ", ".join(["%s"] * len(insert_cols))
    col_sql = ", ".join(f"`{c}`" for c in insert_cols)
    sql = f"INSERT INTO kc_entries ({col_sql}) VALUES ({placeholders})"
    params = [values[c] for c in insert_cols]
    return sql, params


def process_single_file(conn, inbox_path: Path, processed_root: Path, failed_root: Path, source: str) -> None:
    entries = parse_file_to_entries(inbox_path)
    log(f"解析完成，條目數={len(entries)}")
    cursor = conn.cursor()
    try:
        for entry in entries:
            sql, params = build_kc_entries_insert(cursor, entry, source)
            cursor.execute(sql, params)

        rel = inbox_path.relative_to(inbox_path.parents[2])
        target = processed_root / rel.parts[2] / inbox_path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(inbox_path), str(target))
        log(f"已將檔案移到 processed: {target}")
    except Exception as e:
        log(f"寫入 DB 或移動檔案時發生錯誤: {repr(e)}")
        rel = inbox_path.relative_to(inbox_path.parents[2])
        target = failed_root / rel.parts[2] / inbox_path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(inbox_path), str(target))
        log(f"已將檔案移到 failed: {target}")


def main(argv: List[str]) -> None:
    source = argv[1] if len(argv) > 1 else DEFAULT_SOURCE

    inbox_dir = INBOX_ROOT / source
    processed_root = PROCESSED_ROOT
    failed_root = FAILED_ROOT

    log(f"INBOX_DIR={inbox_dir}")

    if not inbox_dir.exists():
        log(f"inbox 目前沒有檔案: {inbox_dir}")
        return

    files = sorted([p for p in inbox_dir.iterdir() if p.is_file()], key=lambda p: p.name)

    if not files:
        log(f"inbox 目前沒有檔案: {inbox_dir}")
        return

    log(f"在 inbox 找到 {len(files)} 個檔案")

    env = load_env(ENV_PATH)
    db_cfg = get_db_config(env)

    try:
        conn = get_db_connection(db_cfg)
    except Exception as e:
        log(f"連線資料庫失敗: {repr(e)}")
        for f in files:
            rel = f.relative_to(inbox_dir)
            target = failed_root / source / rel.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(target))
            log(f"已將檔案移到 failed: {target}")
        return

    try:
        for f in files:
            log(f"處理檔案: {f}")
            process_single_file(conn, f, processed_root, failed_root, source)
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main(sys.argv)
EOF
