#!/usr/bin/env python3
import os
import sys
import json
import datetime
import pathlib
import mysql.connector
import yaml
from typing import List, Dict, Any


BASE_DIR = "/srv/cockswain-core/ai-core/knowledge-center"
CONFIG_PATH = os.path.join(BASE_DIR, "config", "sources_public.yaml")
DATA_RAW_PUBLIC = os.path.join(BASE_DIR, "data", "raw", "public")
LOG_PATH = os.path.join(BASE_DIR, "logs", "kc_collect.log")
ENV_PATH = "/srv/cockswain-core/.env"


def log(msg: str) -> None:
    """簡單的 log：寫到 stdout + 檔案"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [collect_public] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # logging 失敗不影響主流程
        pass


def load_env_from_file(env_path: str) -> Dict[str, str]:
    """讀取 /srv/cockswain-core/.env 裡的設定"""
    env: Dict[str, str] = {}
    if not os.path.exists(env_path):
        log(f".env not found at {env_path}, will rely on process env only.")
        return env

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except Exception as e:
        log(f"failed to read .env: {e}")
    return env


def get_db_connection():
    """建立 MySQL 連線（關閉 SSL，避免 dummy ssl 問題）"""
    file_env = load_env_from_file(ENV_PATH)

    def _get(key: str, default: str = None) -> str:
        return os.environ.get(key, file_env.get(key, default))

    host = _get("MYSQL_HOST", "127.0.0.1")
    port = int(_get("MYSQL_PORT", "3306"))
    user = _get("MYSQL_USER", "cockswain_core")
    password = _get("MYSQL_PASSWORD", "")
    database = _get("MYSQL_DATABASE", "cockswain")

    if not password:
        raise RuntimeError("MYSQL_PASSWORD is not set in env or .env")

    log(f"connecting to MySQL at {host}:{port} as {user}, db={database}")

    # ★ 關閉 SSL，不走 dummy ssl.wrap_socket，避免 do_handshake 錯誤
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        autocommit=True,
        ssl_disabled=True,
    )
    return conn


def load_sources(config_path: str) -> List[Dict[str, Any]]:
    """讀取 sources_public.yaml，只留 enabled 的 file 類型"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"sources_public.yaml not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    sources = cfg.get("sources", [])
    enabled_file_sources = [
        s for s in sources
        if s.get("enabled", True) and s.get("type") == "file"
    ]
    return enabled_file_sources


def collect_from_file_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    v0.1：只處理 .txt/.md/.log，一個檔案 = 一筆文件
    """
    src_id = source.get("id")
    path = source.get("path")
    domain = source.get("domain", "general")

    if not path or not os.path.isdir(path):
        log(f"[{src_id}] path not found or not dir: {path}")
        return []

    docs: List[Dict[str, Any]] = []
    base_path = pathlib.Path(path)

    log(f"[{src_id}] scanning directory: {path}")

    for root, dirs, files in os.walk(path):
        for name in files:
            p = pathlib.Path(root) / name

            # v0.1 先限定幾種文字檔
            if p.suffix.lower() not in {".txt", ".md", ".log"}:
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                log(f"[{src_id}] failed to read {p}: {e}")
                continue

            rel_path = p.relative_to(base_path)

            doc = {
                "source_id": src_id,
                "domain": domain,
                "path": str(p),
                "rel_path": str(rel_path),
                "filename": p.name,
                "content": content,
                "collected_at": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
            }
            docs.append(doc)

    log(f"[{src_id}] collected {len(docs)} documents")
    return docs


def write_snapshot_jsonl(snapshot_key: str, docs: List[Dict[str, Any]]) -> str:
    """把收集到的 docs 寫成一個 JSONL 快照"""
    os.makedirs(DATA_RAW_PUBLIC, exist_ok=True)
    filename = f"{snapshot_key}.jsonl"
    out_path = os.path.join(DATA_RAW_PUBLIC, filename)

    log(f"writing snapshot to {out_path}")

    with open(out_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    return out_path


def record_snapshot_db(
    conn,
    snapshot_key: str,
    source_id: str,
    items_count: int,
    started_at: datetime.datetime,
    finished_at: datetime.datetime,
    status: str = "success",
    error_message: str = None,
) -> None:
    """在 kc_snapshots 插入一筆快照紀錄"""
    sql = """
        INSERT INTO kc_snapshots
        (snapshot_key, source_id, source_type, items_count,
         started_at, finished_at, status, error_message)
        VALUES (%s, %s, 'public', %s, %s, %s, %s, %s)
    """

    cur = conn.cursor()
    try:
        cur.execute(
            sql,
            (
                snapshot_key,
                source_id,
                items_count,
                started_at.strftime("%Y-%m-%d %H:%M:%S"),
                finished_at.strftime("%Y-%m-%d %H:%M:%S"),
                status,
                error_message,
            ),
        )
    finally:
        cur.close()


def main():
    started_at = datetime.datetime.now(datetime.timezone.utc)
    ts_key = started_at.strftime("%Y%m%d_%H%M%S")
    snapshot_key = f"public_{ts_key}"

    # 1) 讀取 source 設定
    try:
        sources = load_sources(CONFIG_PATH)
    except Exception as e:
        log(f"failed to load sources: {e}")
        sys.exit(1)

    if not sources:
        log("no enabled file sources found in sources_public.yaml")
        sys.exit(0)

    # 2) 收集所有檔案內容
    all_docs: List[Dict[str, Any]] = []
    for src in sources:
        docs = collect_from_file_source(src)
        all_docs.extend(docs)

    finished_at = datetime.datetime.now(datetime.timezone.utc)
    items_count = len(all_docs)

    if items_count == 0:
        log("no documents collected, skipping snapshot write & DB record")
        sys.exit(0)

    # 3) 寫 JSONL 快照檔
    try:
        write_snapshot_jsonl(snapshot_key, all_docs)
    except Exception as e:
        log(f"failed to write snapshot jsonl: {e}")
        sys.exit(1)

    # 4) 寫入 kc_snapshots
    try:
        conn = get_db_connection()
    except Exception as e:
        log(f"failed to connect DB for snapshot record: {e}")
        sys.exit(1)

    try:
        # v0.1：一個 snapshot 先記第一個 source_id
        first_source_id = sources[0].get("id", "unknown")
        record_snapshot_db(
            conn,
            snapshot_key,
            first_source_id,
            items_count,
            started_at,
            finished_at,
            status="success",
            error_message=None,
        )
        log(
            f"snapshot {snapshot_key} recorded to kc_snapshots with {items_count} items"
        )
    except Exception as e:
        log(f"failed to record snapshot to DB: {e}")
        sys.exit(1)
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
