"""
Core Layer Bindings v1
負責把 Dynamic Pointer 的 L1/L3/L5/L7
綁到「真實 / 或暫時版」的核心處理器上。
"""

from typing import Any, Dict

from .dynamic_pointer import layer_registry
from knowledge_center.internal_bridge import queue_internal_knowledge_request
from knowledge_center.search_kc import search_kc_basic


# === L1: 語意解析層 ===

def l1_core_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    TODO: 之後改成呼叫你真正的 L1 語意解析模組。
    目前先做比 demo 再「正式一點」的 stub。
    """
    question = payload.get("question", "")
    intent = payload.get("intent", "unknown")

    tokens = list(question)

    return {
        "raw": question,
        "intent": intent,
        "tokens": tokens,
        "note": "L1 core handler: 結構化語意結果（暫時版）",
    }


# === L3: 知識查詢層 ===

def l3_core_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    知識中心查詢（暫時版）：
    - 會先嘗試從 KC（kc_entries）抓一些資料回來
    - 同時建立一筆 internal knowledge request，給之後 collector 處理
    """
    question = payload.get("question", "")
    parsed = payload.get("parsed", {})
    intent = payload.get("intent", "unknown")

    # 1) 先嘗試即時搜尋 KC（若失敗會在 search_kc_basic 內部 fallback）
    kc_results = search_kc_basic(question, limit=5)

    # 2) 建立一筆 internal knowledge request 進 tempstore
    queued = queue_internal_knowledge_request(question, intent, parsed)

    return {
        "lookup_query": question,
        "parsed_hint": parsed,
        "results": kc_results,
        "queued_request": queued,
        "note": "L3 core handler: 嘗試查 KC + 建立知識查詢任務（暫時版）",
    }


# === L5: 反思層 ===

def l5_core_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    L5 做簡單的 meta 反思。
    之後可以依照 results 內容做更複雜的邏輯。
    """
    question = payload.get("question", "")
    knowledge = payload.get("knowledge", {})
    results = knowledge.get("results") or []

    if results:
        comment = f"（L5）已取得 {len(results)} 筆 KC 結果，可以基於這些資料做更深入的反思。"
    else:
        comment = "（L5）目前仍缺少 KC 結果，之後需要補強知識查詢模組。"

    return {
        "question": question,
        "comment": comment,
        "note": "L5 core handler: 簡易版反思（暫時版）",
    }


# === L7: 共識 / 決策層 ===

def l7_core_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    L7 目前先做「總結 + 將中繼資料帶出」。
    未來可以在這裡實作真正的共識演算法。
    """
    question = payload.get("question", "")
    parsed = payload.get("parsed", {})
    knowledge = payload.get("knowledge", {})
    reflection = payload.get("reflection", {})

    answer = (
        f"針對「{question}」，L7 共識結論是：目前動態指向已啟動，"
        f"接下來應逐步替換各層為真實模組，並將內部對話紀錄與知識查詢任務納入知識處理中心，"
        f"作為舵手自我成長的基底。"
    )

    return {
        "answer": answer,
        "parsed": parsed,
        "knowledge": knowledge,
        "reflection": reflection,
        "note": "L7 core handler: 共識結論暫時版",
    }


# === 將 handler 綁到 LayerRegistry ===

def register_core_layers() -> None:
    layer_registry.register("L1", l1_core_handler)
    layer_registry.register("L3", l3_core_handler)
    layer_registry.register("L5", l5_core_handler)
    layer_registry.register("L7", l7_core_handler)
