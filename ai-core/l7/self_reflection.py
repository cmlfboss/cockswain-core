# /srv/cockswain-core/ai-core/l7/self_reflection.py
from pathlib import Path
from datetime import datetime
import json


class SelfReflection:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.log_dir = Path("/srv/cockswain-core/logs/reflection")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def record(self, fused_ctx: dict, goal_ctx: dict, decision: dict, actions: list[dict]):
        ts = datetime.utcnow().timestamp()
        path = self.log_dir / f"l7_reflection_{ts}.json"
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "fused_ctx": fused_ctx,
            "goal_ctx": goal_ctx,
            "decision": decision,
            "actions": actions,
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
