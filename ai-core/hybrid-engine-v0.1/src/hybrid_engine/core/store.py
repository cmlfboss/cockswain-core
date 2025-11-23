from __future__ import annotations

import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# ============================================================
# v0.1 過渡版的 store.py
# 目標：避免 hybrid-engine 因向量庫 schema 不完整而 500
#       → 暫時不啟用 RAG，只存單純 notes 記錄
# ============================================================

DB_PATH = Path("/srv/cockswain-core/var/knowledge/notes.sqlite3")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Internal: get sqlite connection
# ------------------------------------------------------------
def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


# ------------------------------------------------------------
# Init DB
# ------------------------------------------------------------
def init_db():
    with _get_conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                ts   INTEGER NOT NULL,
                role TEXT    NOT NULL,
                text TEXT    NOT NULL,
                meta TEXT    NULL
            );
            """
        )


# ------------------------------------------------------------
# Add note
# ------------------------------------------------------------
def add_note(role: str, text: str, meta: Optional[Dict[str, Any]] = None) -> int:
    ts = int(time.time())
    meta_json = json.dumps(meta or {}, ensure_ascii=False)
    with _get_conn() as c:
        cur = c.execute(
            "INSERT INTO notes (ts, role, text, meta) VALUES (?, ?, ?, ?)",
            (ts, role, text, meta_json),
        )
        return int(cur.lastrowid)


# ------------------------------------------------------------
# Query notes (simple)
# ------------------------------------------------------------
def list_notes(limit: int = 50) -> List[Dict[str, Any]]:
    with _get_conn() as c:
        rows = c.execute(
            "SELECT id, ts, role, text, meta FROM notes ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

        out: List[Dict[str, Any]] = []
        for r in rows:
            try:
                meta_obj = json.loads(r["meta"]) if r["meta"] else {}
            except Exception:
                meta_obj = {}

            out.append(
                {
                    "id": r["id"],
                    "ts": r["ts"],
                    "role": r["role"],
                    "text": r["text"],
                    "meta": meta_obj,
                }
            )
        return out


# ------------------------------------------------------------
# Vector search (disabled in v0.1)
# ------------------------------------------------------------
def search_by_vector(vec, k: int = 5) -> List[Dict[str, Any]]:
    """
    v0.1 暫時關閉 RAG：
    - 不使用向量資料庫
    - 直接回傳空陣列，避免 schema 問題 (v.vec_json not exists)
    """
    return []
