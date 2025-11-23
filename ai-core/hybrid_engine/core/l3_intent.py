from typing import Dict, Any


def build_intent(l1_data: Dict[str, Any], l2_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    L3：真實需求拆解
    - 把 L1 + L2 組合成「intent + 參數」
    """
    intent = l2_data.get("action", "none")
    params: Dict[str, Any] = {}

    text = l1_data.get("clean", "")
    lang = l1_data.get("lang", "en")

    if intent == "list-files":
        # 非常簡化版：預設路徑為 /home/cocksmain
        default_path = "/home/cocksmain"
        params["path"] = default_path

    return {
        "intent": intent,
        "params": params,
        "lang": lang,
        "safe": True,  # 之後可接安全檢查
    }
