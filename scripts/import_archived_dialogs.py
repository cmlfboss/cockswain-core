#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_archived_dialogs.py
將 /srv/cockswain-core/archive/dialog/ 底下的 tar.gz 對話歸檔
一次性匯入到 MySQL
"""
import os
import tarfile
import tempfile
import shutil
import datetime
from pathlib import Path

try:
    import mysql.connector
except ImportError:
    raise SystemExit("請先安裝 mysql-connector-python: sudo apt install python3-mysql.connector")

BASE_DIR = Path("/srv/cockswain-core")
ARCHIVE_DIR = BASE_DIR / "archive" / "dialog"
IMPORTED_DIR = BASE_DIR / "archive" / "imported"
LOG_FILE = BASE_DIR / "logs" / "import_archived_dialogs.log"
ENV_FILE = BASE_DIR / ".env"


def load_env(env_path: Path):
    env = {}
    if env_path.exists():
        with env_path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def get_db_conn(env):
    # 關掉 SSL，避免系統 ssl 模組不完整
    conn = mysql.connector.connect(
        host=env.get("MYSQL_HOST", "127.0.0.1"),
        port=int(env.get("MYSQL_PORT", "3306")),
        user=env.get("MYSQL_USER", "root"),
        password=env.get("MYSQL_PASSWORD", ""),
        database=env.get("MYSQL_DATABASE", "cockswain"),
        ssl_disabled=True,
    )
    return conn


def ensure_table(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS dialog_archive (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        archive_name VARCHAR(255) NOT NULL,
        src_file VARCHAR(255) DEFAULT NULL,
        host VARCHAR(100) DEFAULT NULL,
        created_at DATETIME NOT NULL,
        content LONGTEXT,
        raw_meta JSON NULL
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")


def import_one_archive(conn, archive_path: Path):
    archive_name = archive_path.name
    tmpdir = tempfile.mkdtemp(prefix="dialog-import-")
    try:
        # 解壓縮
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(tmpdir)

        # 找 .txt
        txt_files = list(Path(tmpdir).glob("*.txt"))
        if not txt_files:
            log(f"WARNING: {archive_name} 裡面沒有 .txt，跳過")
            return False

        txt_file = txt_files[0]
        content = txt_file.read_text(encoding="utf-8", errors="ignore")

        created_at = datetime.datetime.now()
        host = os.uname().nodename

        cur = conn.cursor()
        insert_sql = """
            INSERT INTO dialog_archive (archive_name, src_file, host, created_at, content, raw_meta)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            insert_sql,
            (archive_name, txt_file.name, host, created_at, content, None),
        )
        conn.commit()
        cur.close()

        log(f"OK: 匯入 {archive_name} 成功")
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    env = load_env(ENV_FILE)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    IMPORTED_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_db_conn(env)
    ensure_table(conn)

    archives = sorted(ARCHIVE_DIR.glob("*.tar.gz"))
    if not archives:
        log("沒有可匯入的檔案，結束")
        conn.close()
        return

    for archive_path in archives:
        ok = import_one_archive(conn, archive_path)
        if ok:
            target = IMPORTED_DIR / archive_path.name
            archive_path.rename(target)
        else:
            log(f"ERROR: 匯入失敗 {archive_path.name}")

    conn.close()


if __name__ == "__main__":
    main()
