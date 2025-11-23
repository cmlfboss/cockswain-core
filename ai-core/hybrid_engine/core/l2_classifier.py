from typing import Dict, Any


def classify_task(l1_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    L2：粗略任務分類
    - 很簡化的規則：之後可以接 AI 模型再強化
    """
    text = l1_data.get("clean", "").lower()
    lang = l1_data.get("lang", "en")

    category = "qa"          # 問答
    action = "none"

    # 很粗的判斷：有「檔案 / 列出 / 刪除」→ 視為自動化
    if lang == "zh":
        if any(k in text for k in ["列出", "清單", "檔案", "目錄", "搬移", "刪除"]):
            category = "automation"
    else:
        if any(k in text for k in ["list", "file", "folder", "delete", "move", "copy"]):
            category = "automation"

    if category == "automation":
        if "列出" in text or "list" in text:
            action = "list-files"

    return {
        "category": category,
        "action": action,
        "classified": True,
    }
