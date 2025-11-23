#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Center - process_inbox (v4 - 動態 source_id 版)

功能：
- 掃描 inbox 目錄 (目前對應 openai 渠道)
- 每個檔案解析成一個「知識條目」
- 寫入 kc_entries：
    - source_id  -> 由 kc_sources 自動查第一筆 id
    - entry_type -> 'note'
    - author     -> 'openai'
    - role       -> 'system'
    - created_at -> 現在時間
    - content    -> 檔案全文
- 成功的檔案移到 processed，失敗的移到 failed
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import mysql.connector
from mysql.connector import Error

# ---- 讓我們可以從 ai-core 根目錄匯入 database_core ----

CURRENT_FILE = Path(__file__).resolve()
AI_CORE_DIR = CURRENT_FILE.parents[1]  # /srv/cockswain-core/ai-core
if str(AI_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_CORE_DIR))

from database_core import get_db_connection  # type: ignore


# ---- 路徑設定 ----

KC_DIR = CURRENT_FILE.parent
INBOX_DIR = KC_DIR / "inbox" / "openai"
PROCESSED_DIR = KC_DIR / "processed" / "openai"
FAILED_DIR = KC_DIR / "failed" / "openai"

for d in (INBOX_DIR, PROCESSED_DIR, FAILED_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ---- 工具函式 ----

def log(msg: str) -> None:
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print(f"[{now}] [kc] {msg}")


def parse_note_file(path: Path) -> List[Dict]:
    """
    目前簡化處理：
    - 整個檔案內容當成 content
    - 其他欄位用固定值填入（除了 source_id，在 insert 時決定）
    """
    try:
        text = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        text = path.read_text(errors="ignore").strip()

    if not text:
        return []

    entry = {
        "entry_type": "note",            # 之後可做型別區分
        "author": "openai",              # 來源描述
        "role": "system",                # 或 'user' 看你之後怎麼定義
        "created_at": datetime.now(),
        "content": text,
    }
    return [entry]


def get_default_source_id(conn: mysql.connector.connection.MySQLConnection) -> int:
    """
    從 kc_sources 找一個可用的 source_id：
    - 目前策略：拿最小的那一筆 id
    - 若完全沒有資料，直接丟錯，請你先建一筆 kc_sources
    """
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM kc_sources ORDER BY id ASC LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise RuntimeError(
                "kc_sources 目前沒有任何資料，請先在 kc_sources 建立至少一筆來源，"
                "例如 'openai_inbox'，再重新執行 kc_process_inbox。"
            )
        return int(row[0])
    finally:
        cur.close()


def insert_entries(conn: mysql.connector.connection.MySQLConnection,
                   entries: List[Dict]) -> int:
    """
    把 entries 寫入 kc_entries。

    針對目前 kc_entries 的欄位：
        id, source_id, entry_type, author, role,
        created_at, content, semantic_seed, eco_path,
        semantic_path, tags_json, extra_json

    這裡寫入：
        source_id, entry_type, author, role, created_at, content
    其他欄位讓 DB 走預設值 / NULL。
    """
    if not entries:
        return 0

    source_id = get_default_source_id(conn)
    log(f"[db] 使用 source_id={source_id}")

    sql = """
        INSERT INTO kc_entries
            (source_id, entry_type, author, role, created_at, content)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    cur = conn.cursor()
    rows = 0
    try:
        for e in entries:
            created_at = e["created_at"]
            if isinstance(created_at, datetime):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at_str = str(created_at)

            cur.execute(
                sql,
                (
                    source_id,
                    e["entry_type"],
                    e["author"],
                    e["role"],
                    created_at_str,
                    e["content"],
                ),
            )
            rows += 1
        conn.commit()
        return rows
    finally:
        cur.close()


# ---- 主流程 ----

def process_inbox() -> None:
    log(f"INBOX_DIR={INBOX_DIR}")

    files = sorted(INBOX_DIR.glob("*.txt"))
    if not files:
        log(f"inbox 目前沒有檔案: {INBOX_DIR}")
        return

    log(f"在 inbox 找到 {len(files)} 個檔案")

    try:
        conn = get_db_connection(autocommit=False)
    except Error as e:
        log(f"[db] 連線失敗: {e}")
        # 不敢亂移動檔案，全部留下來讓你後續處理
        return

    for path in files:
        log(f"處理檔案: {path}")
        try:
            entries = parse_note_file(path)
            log(f"解析完成，條目數={len(entries)}")

            if entries:
                inserted = insert_entries(conn, entries)
                log(f"[db] 寫入 kc_entries 成功 rows={inserted}")
            else:
                log(f"[warn] 檔案內容為空，略過: {path.name}")

            # 全部成功才移到 processed
            target = PROCESSED_DIR / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))
        except Exception as e:
            log(f"寫入 DB 或移動檔案時發生錯誤: {repr(e)}")
            # 發生錯誤就把檔案丟到 failed
            try:
                target = FAILED_DIR / path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))
                log(f"已將檔案移到 failed: {target}")
            except Exception as e2:
                log(f"[嚴重] 檔案無法移動到 failed: {repr(e2)}")

    conn.close()


if __name__ == "__main__":
    process_inbox()
