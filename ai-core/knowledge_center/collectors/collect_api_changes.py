#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_api_changes.py

用途：
- 定期抓取「外部 / 內部 API 的版本資訊」
- 目前先實作 Meilisearch 本地節點的 version 追蹤
- 偵測版本變更後，寫入 MySQL 資料表 kc_api_changes

相依：
- /srv/cockswain-core/.env 內需包含：
    MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
    （可同 collect_public 使用的設定）
- sources_api.yaml 格式（範例）：
    sources:
      - id: meilisearch_local
        enabled: true
        type: "http_json"
        base_url: "http://127.0.0.1:7700"
        version_path: "/version"
        freq: "weekly"
        domain: "search"
        track:
          - "version"
        api_key_env: "MEILI_MASTER_KEY"
        tags: ["internal", "infra"]
"""

import os
import sys
import json
import datetime
import pathlib
from typing import Any, Dict, List, Optional, Tuple

import mysql.connector
import yaml

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ------------------------------------------------------------
# 基本路徑設定
# ------------------------------------------------------------

BASE_DIR = "/srv/cockswain-core/ai-core/knowledge-center"
CONFIG_PATH = os.path.join(BASE_DIR, "config", "sources_api.yaml")

CORE_ROOT = "/srv/cockswain-core"
DOT_ENV_PATH = os.path.join(CORE_ROOT, ".env")


# ------------------------------------------------------------
# 小工具：log, env, YAML
# ------------------------------------------------------------

def log(msg: str) -> None:
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [collect_api_changes] {msg}")


def load_env(env_path: str) -> Dict[str, str]:
    """
    讀取簡單版 .env（KEY=VALUE），忽略註解與空行。
    """
    env: Dict[str, str] = {}
    if not os.path.exists(env_path):
        log(f"env file not found at {env_path}, skip loading .env")
        return env

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env[key] = value
        log(f"loaded env from {env_path}")
    except Exception as e:
        log(f"failed to load env from {env_path}: {e!r}")
    return env


def load_sources(config_path: str) -> List[Dict[str, Any]]:
    """
    讀取 sources_api.yaml:
    - 預期格式：
        sources:
          - id: meilisearch_local
            enabled: true
            ...
    """
    if not os.path.exists(config_path):
        log(f"config not found: {config_path}")
        return []

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        sources = data.get("sources") or []
        log(f"loaded {len(sources)} api sources from {config_path}")
        return sources
    except Exception as e:
        log(f"failed to load config {config_path}: {e!r}")
        return []


# ------------------------------------------------------------
# MySQL 連線與版本紀錄操作
# ------------------------------------------------------------

def get_db_connection(env: Dict[str, str]):
    """
    建立 MySQL 連線：
    - 使用舵手專用帳號 cockswain_core
    - 禁用 SSL（避免 Debian/Ubuntu python3.12 的 ssl _dummy_wrap_socket 問題）
    """
    db_host = env.get("MYSQL_HOST", "127.0.0.1")
    db_port_raw = env.get("MYSQL_PORT", "3306")
    try:
        db_port = int(db_port_raw)
    except ValueError:
        db_port = 3306

    db_name = env.get("MYSQL_DATABASE", "cockswain")
    db_user = env.get("MYSQL_USER", "cockswain_core")
    db_password = env.get("MYSQL_PASSWORD", "")

    log(f"connecting to MySQL at {db_host}:{db_port} as {db_user}, db={db_name}")

    conn = mysql.connector.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        autocommit=False,
        ssl_disabled=True,  # 關鍵：不要走 SSL，避免 wrap_socket dummy
    )
    return conn


def get_last_version(conn, source_id: str) -> Optional[str]:
    """
    從 kc_api_changes 取出最新一筆 new_version。
    """
    sql = """
        SELECT new_version
        FROM kc_api_changes
        WHERE source_id = %s
        ORDER BY detected_at DESC, id DESC
        LIMIT 1
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, (source_id,))
        row = cur.fetchone()
        if not row:
            return None
        return row[0]
    finally:
        cur.close()


def classify_change(prev_version: Optional[str], new_version: Optional[str]) -> str:
    """
    粗略判斷版本變更類型：major / minor / patch / unknown
    - 假設格式為「x.y.z」，不符合則一律 unknown
    """
    if not new_version:
        return "unknown"
    if not prev_version:
        return "unknown"

    def parse(v: str) -> Optional[Tuple[int, int, int]]:
        parts = v.split(".")
        if len(parts) < 3:
            return None
        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
            return (major, minor, patch)
        except ValueError:
            return None

    p_old = parse(prev_version)
    p_new = parse(new_version)
    if not p_old or not p_new:
        return "unknown"

    if p_new[0] != p_old[0]:
        return "major"
    if p_new[1] != p_old[1]:
        return "minor"
    if p_new[2] != p_old[2]:
        return "patch"
    return "unknown"


def record_version_change(
    conn,
    source_id: str,
    prev_version: Optional[str],
    new_version: str,
    change_type: str,
    raw_json: Dict[str, Any],
) -> None:
    """
    寫入 kc_api_changes。
    """
    detected_at = datetime.datetime.utcnow()
    raw_diff_obj = {
        "prev_version": prev_version,
        "new_version": new_version,
        "raw": raw_json,
    }
    raw_diff_json = json.dumps(raw_diff_obj, ensure_ascii=False)

    sql = """
        INSERT INTO kc_api_changes
            (source_id, prev_version, new_version, change_type, detected_at, raw_diff, note)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """
    note = "auto-detected by collect_api_changes"

    cur = conn.cursor()
    try:
        cur.execute(
            sql,
            (
                source_id,
                prev_version,
                new_version,
                change_type,
                detected_at,
                raw_diff_json,
                note,
            ),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        log(f"[{source_id}] failed to insert kc_api_changes: {e!r}")
        raise
    finally:
        cur.close()


# ------------------------------------------------------------
# Meilisearch 版本抓取
# ------------------------------------------------------------

def fetch_meili_version(source: Dict[str, Any], env: Dict[str, str]) -> Tuple[str, Dict[str, Any]]:
    """
    呼叫 Meilisearch /version，回傳 (version_str, raw_json)。
    - 會依照 source["api_key_env"] 或 env["MEILI_MASTER_KEY"] 設定 Authorization header。
    - version 主要取 pkgVersion，備援用 version 或 commitSha。
    """
    base_url = source.get("base_url", "http://127.0.0.1:7700").rstrip("/")
    version_path = source.get("version_path", "/version")
    if not version_path.startswith("/"):
        version_path = "/" + version_path

    url = base_url + version_path

    # 取得 API key env 變數名稱
    api_key_env = source.get("api_key_env") or "MEILI_MASTER_KEY"
    api_key = env.get(api_key_env) or env.get("MEILI_MASTER_KEY")

    headers = {
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    log(f"[{source.get('id','unknown')}] fetching {url} with Authorization: {'yes' if api_key else 'no'}")

    req = Request(url, headers=headers, method="GET")

    try:
        with urlopen(req, timeout=5) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        log(
            f"[{source.get('id','unknown')}] HTTPError while fetching version: "
            f"status={e.code}, reason={getattr(e, 'reason', '')}"
        )
        raise
    except URLError as e:
        log(f"[{source.get('id','unknown')}] URLError while fetching version: {e.reason}")
        raise
    except Exception as e:
        log(f"[{source.get('id','unknown')}] unexpected error while fetching version: {e!r}")
        raise

    if status != 200:
        log(f"[{source.get('id','unknown')}] non-200 status: {status}, body={body[:200]}")
        raise RuntimeError(f"non-200 status: {status}")

    try:
        data = json.loads(body)
    except Exception as e:
        log(f"[{source.get('id','unknown')}] failed to parse JSON: {e!r}, body={body[:200]}")
        raise

    # Meilisearch v1.11 會回傳：
    # {"commitSha": "...", "commitDate": "...", "pkgVersion":"1.11.0"}
    version = (
        data.get("pkgVersion")
        or data.get("version")
        or data.get("commitSha")
        or ""
    )

    if not version:
        log(f"[{source.get('id','unknown')}] version field missing in response JSON: {data}")
        raise RuntimeError("version field missing in Meilisearch response")

    return version, data


def process_meili_source(conn, source: Dict[str, Any], env: Dict[str, str]) -> None:
    """
    處理單一 Meilisearch source：
    - 讀取上一個版本
    - 抓取現在版本
    - 若有變化則寫入 kc_api_changes
    """
    source_id = source.get("id", "unknown")

    try:
        last_version = get_last_version(conn, source_id)
    except Exception as e:
        log(f"[{source_id}] failed to get last_version: {e!r}")
        last_version = None

    try:
        current_version, raw_json = fetch_meili_version(source, env)
    except Exception as e:
        log(f"[{source_id}] failed to fetch current version: {e!r}")
        return

    if current_version == last_version and last_version is not None:
        log(f"[{source_id}] version unchanged: {current_version}")
        return

    change_type = classify_change(last_version, current_version)

    log(
        f"[{source_id}] version changed: {last_version} -> {current_version} "
        f"(type={change_type})"
    )

    try:
        record_version_change(
            conn=conn,
            source_id=source_id,
            prev_version=last_version,
            new_version=current_version,
            change_type=change_type,
            raw_json=raw_json,
        )
    except Exception:
        # record_version_change 已經 log & rollback，這裡再補一行
        log(f"[{source_id}] failed to record version change in kc_api_changes")


# ------------------------------------------------------------
# main
# ------------------------------------------------------------

def main(argv: List[str]) -> int:
    # 載 env（給 MySQL & Meili API key 用）
    env = load_env(DOT_ENV_PATH)

    # 載 sources_api.yaml
    sources = load_sources(CONFIG_PATH)

    if not sources:
        log("no api sources configured, exit")
        return 0

    # 建立 DB 連線
    try:
        conn = get_db_connection(env)
    except Exception as e:
        log(f"failed to connect DB: {e!r}")
        return 1

    try:
        for src in sources:
            if not src.get("enabled", True):
                continue

            src_id = src.get("id", "unknown")
            src_type = src.get("type", "http")
            track = src.get("track") or []

            # 目前僅處理 Meilisearch 類型：
            # - type 為 http / http_json
            # - track 包含 "version" 或未設定 track
            if src_type in ("http", "http_json") and ("version" in track or not track):
                process_meili_source(conn, src, env)
            else:
                log(f"[{src_id}] skip type={src_type}, track={track}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
