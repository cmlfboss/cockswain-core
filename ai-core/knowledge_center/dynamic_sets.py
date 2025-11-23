import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from decimal import Decimal
import mysql.connector


# --- 基本路徑與 .env 載入 ---

ROOT_DIR = Path(__file__).resolve().parents[1]  # /srv/cockswain-core/ai-core
ENV_FILE = ROOT_DIR.parent / ".env"            # /srv/cockswain-core/.env
SNAPSHOT_DIR = ROOT_DIR / "knowledge_center" / "storage" / "datasets"


def load_env(env_path: Path) -> None:
    """
    很單純的 .env 讀取：KEY=VALUE，忽略註解與空行。
    若環境變數已存在就不覆蓋（保留外層設定的優先權）。
    """
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key and key not in os.environ:
                os.environ[key] = val


def get_db_conn():
    """
    依照母機 .env 連線 MySQL。
    重點：禁用 SSL，走本機 plain 連線，避免 do_handshake 那個 bug。
    """
    load_env(ENV_FILE)

    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "cockswain_core")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "cockswain")
    port = int(os.getenv("DB_PORT", "3306"))

    cfg = {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "port": port,
        # 關鍵：明確要求不要走 SSL
        "ssl_disabled": True,
    }

    return mysql.connector.connect(**cfg)


# --- JSON 正規化工具 ---

def _normalize_value(v: Any) -> Any:
    """
    把 DB 撈出的值轉成可以被 json 序列化的型別。
    """
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        # 視情況可以改成 str(v)
        return float(v)
    # 其它型別直接丟給 json 自己處理
    return v


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _normalize_value(v) for k, v in row.items()}


# --- 動態資料集的 DB 操作 ---

def list_datasets() -> List[Dict[str, Any]]:
    """
    列出所有已註冊的動態資料集（kc_dynamic_datasets）。
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
              id,
              dataset_code,
              name,
              description,
              source_table,
              where_clause,
              order_by_clause,
              limit_size,
              enabled,
              created_at,
              updated_at
            FROM kc_dynamic_datasets
            ORDER BY dataset_code ASC;
            """
        )
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def get_dataset_by_code(dataset_code: str) -> Optional[Dict[str, Any]]:
    """
    依 dataset_code 取得單一動態資料集定義。
    僅抓 enabled=1 的。
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
              id,
              dataset_code,
              name,
              description,
              source_table,
              where_clause,
              order_by_clause,
              limit_size,
              enabled,
              created_at,
              updated_at
            FROM kc_dynamic_datasets
            WHERE dataset_code = %s
              AND enabled = 1
            LIMIT 1;
            """,
            (dataset_code,),
        )
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def query_dataset_rows(ds: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    根據 kc_dynamic_datasets 的設定去查實際資料表，輸出 rows（list of dict）。
    目前先支援：
      - 單一 source_table
      - WHERE / ORDER BY / LIMIT 都由 ds 決定
    """
    source_table = ds["source_table"]
    where_clause = ds.get("where_clause") or ""
    order_by_clause = ds.get("order_by_clause") or ""
    limit_size = ds.get("limit_size") or 1000

    # 基本 SELECT *
    sql = f"SELECT * FROM {source_table}"
    params: list[Any] = []

    if where_clause.strip():
        sql += f" WHERE {where_clause}"

    if order_by_clause.strip():
        sql += f" ORDER BY {order_by_clause}"

    # 最後加上 LIMIT，避免炸出過多資料
    sql += " LIMIT %s"
    params.append(int(limit_size))

    conn = get_db_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def build_dataset_snapshot(dataset_code: str) -> Path:
    """
    針對指定 dataset_code 建立一次「快照檔」：
      - 會讀 kc_dynamic_datasets 的設定
      - 查詢 source_table 的實際資料
      - 存成 JSON 檔案（含 meta）
    檔名格式：
      storage/datasets/{dataset_code}_{YYYYmmdd_HHMMSS}.json
    """
    ds = get_dataset_by_code(dataset_code)
    if not ds:
        raise RuntimeError(f"dataset_code='{dataset_code}' 不存在或未啟用 (enabled=1)。")

    rows = query_dataset_rows(ds)
    # 🔑 把每一 row 做 JSON 正規化
    norm_rows = [_normalize_row(r) for r in rows]

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now()
    ts_str = now.strftime("%Y%m%d_%H%M%S")
    out_file = SNAPSHOT_DIR / f"{dataset_code}_{ts_str}.json"

    payload = {
        "meta": {
            "dataset_code": ds["dataset_code"],
            "name": ds["name"],
            "description": ds.get("description"),
            "source_table": ds["source_table"],
            "generated_at": now.isoformat(),
            "row_count": len(norm_rows),
        },
        "rows": norm_rows,
    }

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return out_file


# --- CLI 入口 ---

def cli_list() -> None:
    rows = list_datasets()
    if not rows:
        print("[datasets] 目前沒有任何動態資料集定義（kc_dynamic_datasets 為空）。")
        return

    print("[datasets] 動態資料集列表：")
    for ds in rows:
        status = "ENABLED" if ds["enabled"] else "DISABLED"
        print(f"- {ds['dataset_code']} [{status}]")
        print(f"    name    : {ds['name']}")
        if ds.get("description"):
            print(f"    desc    : {ds['description']}")
        print(f"    table   : {ds['source_table']}")
        if ds.get("where_clause"):
            print(f"    where   : {ds['where_clause']}")
        if ds.get("order_by_clause"):
            print(f"    order by: {ds['order_by_clause']}")
        print(f"    limit   : {ds.get('limit_size')}")
        print("")


def cli_build(dataset_code: str) -> None:
    out_file = build_dataset_snapshot(dataset_code)
    print(f"[datasets] dataset={dataset_code} snapshot 建立完成：{out_file}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法：")
        print("  python -m knowledge_center.dynamic_sets list")
        print("  python -m knowledge_center.dynamic_sets build <dataset_code>")
        raise SystemExit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        cli_list()
    elif cmd == "build":
        if len(sys.argv) < 3:
            print("缺少 dataset_code")
            raise SystemExit(1)
        dataset_code = sys.argv[2]
        cli_build(dataset_code)
    else:
        print(f"未知指令：{cmd}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
