"""
Internal → Knowledge Center Bridge v1
- 負責把「舵手內部對話」產生的知識查詢需求，丟到 tempstore。
- 之後可以由獨立的 collector 腳本去處理這些 JSON 任務。
"""

import os
import json
import uuid
import datetime
from typing import Any, Dict

BASE_DIR = "/srv/cockswain-core/ai-core/tempstore/kc_internal_requests"


def queue_internal_knowledge_request(
    question: str,
    intent: str,
    parsed: Dict[str, Any],
) -> Dict[str, Any]:
    """
    建立一個知識查詢請求 JSON 檔，回傳 request_id 與檔案路徑。
    """
    os.makedirs(BASE_DIR, exist_ok=True)

    request_id = str(uuid.uuid4())
    ts = datetime.datetime.utcnow().isoformat()

    payload = {
        "request_id": request_id,
        "created_at": ts,
        "question": question,
        "intent": intent,
        "parsed": parsed,
        "status": "queued",
        "source": "internal_dialogue",
    }

    filename = f"{ts.replace(':', '').replace('-', '')}_{request_id}.json"
    filepath = os.path.join(BASE_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {
        "request_id": request_id,
        "path": filepath,
    }
