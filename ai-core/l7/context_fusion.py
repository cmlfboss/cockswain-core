# /srv/cockswain-core/ai-core/l7/context_fusion.py
from datetime import datetime


class ContextFusion:
    """
    把多層 payload 融合成一個 fused_ctx
    現在是很單純的合併
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def fuse(self, layers_payload: dict) -> dict:
        fused = {
            "timestamp": datetime.utcnow().isoformat(),
            "raw": layers_payload,
        }

        # L1 語意
        l1 = layers_payload.get("l1") or {}
        fused["semantic"] = l1.get("semantic")

        # L4 邏輯
        l4 = layers_payload.get("l4") or {}
        fused["logic"] = l4 if l4 else None

        # L6 系統狀態
        l6 = layers_payload.get("l6") or {}
        fused["system_state"] = l6.get("system_state") if l6 else None

        # 模擬 goal_alignment
        intent = (l1.get("semantic") or {}).get("intent", "unknown")
        fused["goal_alignment"] = {
            "intent": intent,
            "aligned_goals": [
                "peaceful_coexistence",
                "mutual_help",
                "gradual_self_strengthening",
            ],
            "deviation": 0.0,
        }

        return fused
