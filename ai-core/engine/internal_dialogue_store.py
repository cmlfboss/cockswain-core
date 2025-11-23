"""
Internal Dialogue Store v1
負責把 internal dialogue 的結果，先存成 JSON 檔。
未來可以再加：寫入 DB、送進知識處理中心等。
"""

import os
import json
import datetime
from typing import Any, Dict

from .dynamic_pointer import run_internal_dialogue
from .core_layer_bindings import register_core_layers

# 日誌路徑先對齊你原本的 /srv/cockswain-core/logs
BASE_LOG_DIR = "/srv/cockswain-core/logs/internal_dialogues"


def save_dialogue_to_file(result: Dict[str, Any]) -> str:
    """
    將 run_internal_dialogue(...) 的結果存成一個 JSON 檔。

    檔名格式：
        YYYYMMDD_HHMMSS_<intent>.json
    """
    os.makedirs(BASE_LOG_DIR, exist_ok=True)

    intent = result.get("intent", "unknown_intent")
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    filename = f"{ts}_{intent}.json"
    filepath = os.path.join(BASE_LOG_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return filepath


def run_and_store_internal_dialogue(question: str, intent: str = "default") -> Dict[str, Any]:
    """
    一次搞定：
    1) 註冊核心層 handler
    2) 跑 internal dialogue 管線
    3) 存成 JSON 檔
    4) 回傳 result（包含 final + history）

    之後任何模組只要想用「舵手內部會議」，可以直接呼叫這個。
    """
    register_core_layers()
    result = run_internal_dialogue(question, intent=intent)
    path = save_dialogue_to_file(result)
    result["_saved_path"] = path
    return result
