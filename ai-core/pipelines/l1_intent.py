from . import intent_classifier

def process(data: dict, ctx: dict):
    text = data.get("text", "") or ""

    # 第一層：粗分
    is_task = any(k in text for k in ["安裝", "建設", "節點", "匯入", "部署"])
    data["l1_intent"] = "task" if is_task else "chat"

    # 第二層：細分（塞進 l1_intent_detail）
    detail = intent_classifier.classify(text)
    data["l1_intent_detail"] = detail

    return data
