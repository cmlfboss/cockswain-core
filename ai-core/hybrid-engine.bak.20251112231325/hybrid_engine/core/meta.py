import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

class MetaLog:
    LOG_FILE = Path("/srv/cockswain-core/logs/hybrid_engine_meta.log")

    @classmethod
    def record(cls, tag: str, payload: Optional[Dict[str, Any]] = None) -> None:
        rec: Dict[str, Any] = {"tag": tag, "ts": time.time()}
        if isinstance(payload, dict):
            rec.update(payload)
        try:
            cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with cls.LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as e:
            # 錯誤也盡量落檔（避免再丟例外）；不用 f-string，保守穩定
            err = cls.LOG_FILE.with_suffix(".err.log")
            try:
                ts = time.strftime('%Y-%m-%d %H:%M:%S')
                with err.open("a", encoding="utf-8") as ef:
                    ef.write("[{}] write-fail: {}\n".format(ts, e))
            except Exception:
                pass

def log_meta(tag: str, payload: Optional[Dict[str, Any]] = None) -> None:
    """向後相容舊呼叫點"""
    MetaLog.record(tag, payload or {})
