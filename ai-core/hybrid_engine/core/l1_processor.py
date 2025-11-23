import re
from datetime import datetime
from typing import Dict, Any


def normalize_input(raw_text: str, source: str = "unknown") -> Dict[str, Any]:
    """
    L1：標準化輸入
    - 清理空白 / 控制字元
    - 粗略偵測語言（先簡化：看到中文就當 zh，否則 en）
    """
    text = raw_text.strip()
    text = re.sub(r"\s+", " ", text)

    lang = "zh" if re.search(r"[\u4e00-\u9fff]", text) else "en"

    return {
        "raw": raw_text,
        "clean": text,
        "lang": lang,
        "source": source,
        "normalized_at": datetime.utcnow().isoformat() + "Z",
    }
