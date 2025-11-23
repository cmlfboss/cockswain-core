"""
Knowledge Center Basic Search v1
- 先做一個極度安全的基礎搜尋：
  - 嘗試從 kc_entries 撈幾筆資料
  - 查詢策略先簡單：暫時不做真正的全文搜尋，只是 demo 版
- 若資料表不存在或欄位不符，直接回傳空陣列，並印出 warning。
"""

from typing import Any, Dict, List
from knowledge_center.db import get_connection


def search_kc_basic(question: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    極簡版 KC 搜尋：

    - 目前策略：先從 kc_entries 拿出最新幾筆，當作「相關結果 demo」
    - 未來可以改成：
        - MATCH AGAINST
        - Meilisearch
        - 各種 embedding 搜尋
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
        SELECT *
        FROM kc_entries
        ORDER BY id DESC
        LIMIT %s
        """
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARN] search_kc_basic failed: {e}")
        return []

    results: List[Dict[str, Any]] = []

    for row in rows:
        entry_id = row.get("id")
        title = row.get("title") or row.get("name") or ""
        content = (
            row.get("content")
            or row.get("summary")
            or row.get("text")
            or ""
        )

        snippet = content[:200] if isinstance(content, str) else ""

        results.append(
            {
                "entry_id": entry_id,
                "title": title,
                "snippet": snippet,
            }
        )

    return results
