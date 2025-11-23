def classify(text: str) -> str:
    if not text:
        return "unknown"

    t = text.strip()

    # 建設類：安裝、建設、節點、匯入、部署
    if any(k in t for k in ["安裝", "建設", "節點", "匯入", "部署", "母機"]):
        return "build"

    # 系統類：服務、systemd、log、權限、目錄
    if any(k in t for k in ["systemd", "服務", "啟動", "目錄", "權限", "logs", "log"]):
        return "system"

    # 測試類：測試、試跑、驗證、測一下
    if any(k in t for k in ["測試", "驗證", "試跑", "測一下"]):
        return "test"

    # 哲學/治理類：舵手、治理、成長、認知、自我、反思
    if any(k in t for k in ["舵手", "治理", "成長", "認知", "反思", "探索"]):
        return "governance"

    # 回家才能做：回家、家裡、NAS、內網
    if any(k in t for k in ["回家", "家裡", "內網", "家中"]):
        return "home-required"

    return "general"
