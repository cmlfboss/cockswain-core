"""
Knowledge Center DB utilities
提供 get_connection() 給各種 collector 使用。
"""

import os
from typing import Any
import mysql.connector

try:
    from dotenv import load_dotenv
    # 若有 python-dotenv，就載入一下共用 .env
    load_dotenv("/srv/cockswain-core/.env")
except Exception:
    # 沒裝也沒關係，當作環境變數已經由 systemd 載好了
    pass


def get_connection() -> Any:
    """
    建立一個 MySQL 連線。

    預設：
      host    = localhost
      user    = cockswain_core
      db_name = cockswain
      password 從環境變數 DB_PASSWORD（或 MYSQL_PASSWORD）取

    並且強制關閉 SSL（ssl_disabled=True），避免本機連線踩 SSL handshaking 的雷。
    """
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "cockswain_core")
    password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD")
    database = os.getenv("DB_NAME", "cockswain")

    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=True,
        ssl_disabled=True,
    )
    return conn
