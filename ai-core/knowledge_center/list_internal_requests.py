"""
List Internal KC Requests v1.0
- 從 kc_internal_requests 列出最近 N 筆 internal 工單
- 方便你檢查舵手都在對自己提什麼問題
"""

from typing import Any
import datetime

from knowledge_center.db import get_connection


def list_recent_internal_requests(limit: int = 20) -> None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT id, request_uuid, intent, status, created_at, processed_at
    FROM kc_internal_requests
    ORDER BY id DESC
    LIMIT %s
    """

    cursor.execute(sql, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        print("[INFO] 目前 kc_internal_requests 是空的。")
        return

    print(f"=== 最近 {len(rows)} 筆 internal KC requests ===")
    for row in rows:
        print("-" * 60)
        print(f"id          : {row['id']}")
        print(f"request_uuid: {row['request_uuid']}")
        print(f"intent      : {row['intent']}")
        print(f"status      : {row['status']}")
        print(f"created_at  : {row['created_at']}")
        print(f"processed_at: {row['processed_at']}")


def main() -> None:
    list_recent_internal_requests(limit=20)


if __name__ == "__main__":
    main()
