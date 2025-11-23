"""
Collect Internal KC Requests v1.0
- 掃描 tempstore/kc_internal_requests
- 讀取每一個 JSON request
- 寫入 DB: kc_internal_requests
- 將 JSON 移到 kc_internal_processed 並更新 status
"""

import os
import json
import shutil
import datetime
from typing import Any, Dict

from knowledge_center.db import get_connection

REQUEST_DIR = "/srv/cockswain-core/ai-core/tempstore/kc_internal_requests"
PROCESSED_DIR = "/srv/cockswain-core/ai-core/tempstore/kc_internal_processed"


def store_request_in_db(data: Dict[str, Any]) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO kc_internal_requests
      (request_uuid, question, intent, parsed_json, status, source, created_at, processed_at)
    VALUES
      (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      question = VALUES(question),
      intent = VALUES(intent),
      parsed_json = VALUES(parsed_json),
      status = VALUES(status),
      processed_at = VALUES(processed_at)
    """

    request_uuid = data.get("request_id")
    question = data.get("question", "")
    intent = data.get("intent", "")
    parsed = data.get("parsed", {}) or {}
    source = data.get("source", "internal_dialogue")

    created_at_str = data.get("created_at")
    try:
        created_at = datetime.datetime.fromisoformat(created_at_str)
    except Exception:
        created_at = datetime.datetime.utcnow()

    processed_at = datetime.datetime.utcnow()
    status = "stored"

    cursor.execute(
        sql,
        (
            request_uuid,
            question,
            intent,
            json.dumps(parsed, ensure_ascii=False),
            status,
            source,
            created_at.strftime("%Y-%m-%d %H:%M:%S"),
            processed_at.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


def process_request_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    request_id = data.get("request_id", "unknown")
    question = data.get("question", "")
    intent = data.get("intent", "")
    parsed = data.get("parsed", {})

    print("=== 處理 internal KC request ===")
    print(f"request_id: {request_id}")
    print(f"intent    : {intent}")
    print(f"question  : {question}")
    print(f"parsed    : {parsed.get('tokens') or parsed.get('raw')}")
    print("=== 寫入 DB: kc_internal_requests ===")

    # 寫入資料庫
    store_request_in_db(data)

    # 更新 status
    data["status"] = "stored"

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    filename = os.path.basename(path)
    dest_path = os.path.join(PROCESSED_DIR, filename)

    # 移動檔案
    shutil.move(path, dest_path)

    # 覆寫為更新後的 JSON
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"=== 已移動到: {dest_path} 並標記為 stored ===\n")


def main() -> None:
    if not os.path.isdir(REQUEST_DIR):
        print(f"[INFO] 無資料夾: {REQUEST_DIR}")
        return

    files = sorted(
        f for f in os.listdir(REQUEST_DIR)
        if f.endswith(".json")
    )

    if not files:
        print("[INFO] 沒有待處理的 internal KC requests。")
        return

    for name in files:
        path = os.path.join(REQUEST_DIR, name)
        process_request_file(path)


if __name__ == "__main__":
    main()
