"""
Demo handlers for L1 ~ L7，先測試 Dynamic Pointer v1。
之後你可以把這些替換成真的模組呼叫。
"""

from typing import Dict, Any
from .dynamic_pointer import layer_registry


def l1_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 最簡單：把問題拆成詞，當成「語意解析結果」
    question = payload.get("question", "")
    tokens = question.split()
    return {
        "tokens": tokens,
        "note": "L1 demo handler: 粗略 token 切分",
    }


def l3_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Demo：假裝查到一點知識
    question = payload.get("question", "")
    return {
        "facts": [f"（假資料）跟『{question}』相關的知識 A", "（假資料）相關知識 B"],
        "note": "L3 demo handler: 假裝查知識",
    }


def l5_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Demo：假裝做反思，只回傳一個 comment
    return {
        "comment": "（L5 demo）看起來這個問題需要以『動態指向』角度來處理。",
        "note": "L5 demo handler: 簡單反思",
    }


def l7_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Demo：把前面資訊簡單彙整成一句結論
    question = payload.get("question", "")
    return {
        "answer": f"針對「{question}」，目前內部共識是：先完成動態指向核心，才能讓舵手真正自我對話與自我成長。",
        "note": "L7 demo handler: 簡單共識結論",
    }


def register_demo_layers() -> None:
    """
    在系統啟動時呼叫這個，把 demo handlers 掛到 registry。
    之後可以改成真實 handlers。
    """
    layer_registry.register("L1", l1_handler)
    layer_registry.register("L3", l3_handler)
    layer_registry.register("L5", l5_handler)
    layer_registry.register("L7", l7_handler)
