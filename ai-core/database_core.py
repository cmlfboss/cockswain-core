"""
Cockswain Core - Database Helper (強化版 v1)

- 一定會讀 /srv/cockswain-core/.env（就算沒安裝 python-dotenv）
- 強制使用 mysql_native_password
- 強制 ssl_disabled=True，避免 sha256_password requires SSL
- 提供簡單 debug 訊息，幫助確認實際使用的設定
"""

import os
from pathlib import Path
from typing import Dict

import mysql.connector
from mysql.connector import Error, MySQLConnection

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore


# ---- 路徑設定 ----

AI_CORE_DIR = Path(__file__).resolve().parent          # /srv/cockswain-core/ai-core
ROOT_DIR = AI_CORE_DIR.parent                          # /srv/cockswain-core
DEFAULT_ENV_PATH = ROOT_DIR / ".env"


_ENV_LOADED = False
_ENV_CACHE: Dict[str, str] = {}


def _manual_load_env(path: Path) -> None:
    """
    簡單版 .env 解析器：KEY=VALUE 格式，一行一個。
    不支援花式語法，但對我們現在已經足夠。
    """
    global _ENV_CACHE

    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()

        # 去掉包在最外層的單引號或雙引號
        if (val.startswith("'") and val.endswith("'")) or (
            val.startswith('"') and val.endswith('"')
        ):
            val = val[1:-1]

        _ENV_CACHE[key] = val


def _load_env_if_needed() -> None:
    global _ENV_LOADED

    if _ENV_LOADED:
        return

    env_path = DEFAULT_ENV_PATH
    if not env_path.exists():
        # 備用：ai-core/.env
        alt = AI_CORE_DIR / ".env"
        if alt.exists():
            env_path = alt

    # 先用 manual parser 讀一次，確保就算沒有 python-dotenv 也有東西
    _manual_load_env(env_path)

    # 如果有 python-dotenv，再用它把東西塞進 os.environ
    if load_dotenv is not None:
        load_dotenv(dotenv_path=env_path)

    _ENV_LOADED = True


def _get_env(key: str, default: str = "") -> str:
    _load_env_if_needed()

    # 1) 先看 os.environ（允許系統層覆蓋）
    if key in os.environ:
        return os.environ[key]

    # 2) 再看我們 manual parser 的結果
    if key in _ENV_CACHE:
        return _ENV_CACHE[key]

    return default


def _get_db_config() -> dict:
    host = _get_env("DB_HOST", "localhost")
    name = _get_env("DB_NAME", "cockswain")
    user = _get_env("DB_USER", "cockswain_core")
    password = _get_env("DB_PASSWORD", "")

    return {
        "host": host,
        "database": name,
        "user": user,
        "password": password,
    }


def get_db_connection(
    autocommit: bool = True,
) -> MySQLConnection:
    """
    取得一個新的 MySQL 連線。

    - 強制 auth_plugin = mysql_native_password
    - 強制 ssl_disabled = True（避免 sha256_password requires SSL）
    """
    cfg = _get_db_config()

    try:
        conn = mysql.connector.connect(
            host=cfg["host"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            auth_plugin="mysql_native_password",
            ssl_disabled=True,
        )
        conn.autocommit = autocommit
        return conn
    except Error as e:
        # 把實際使用的設定（不含密碼）印出來，方便 debug
        debug_cfg = {
            "host": cfg["host"],
            "database": cfg["database"],
            "user": cfg["user"],
            "password_len": len(cfg["password"]) if cfg["password"] else 0,
        }
        print(f"[database_core] connection failed: {repr(e)}")
        print(f"[database_core] config used: {debug_cfg}")
        raise e


def test_connection() -> bool:
    """
    簡單測試 DB 是否可連線。
    """
    try:
        cfg = _get_db_config()
        debug_cfg = {
            "host": cfg["host"],
            "database": cfg["database"],
            "user": cfg["user"],
            "password_len": len(cfg["password"]) if cfg["password"] else 0,
        }
        print(f"[database_core] testing with config: {debug_cfg}")

        conn = get_db_connection()
        conn.close()
        return True
    except Error:
        return False


if __name__ == "__main__":
    ok = test_connection()
    print(f"[database_core] connection ok={ok}")
