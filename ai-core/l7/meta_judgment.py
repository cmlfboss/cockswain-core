# /srv/cockswain-core/ai-core/l7/meta_judgment.py
from .policy import get_intent_policy


class MetaJudgment:
    """
    v0.2: 照策略表看要不要審核，並把上游的 params 帶下去
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.risk_threshold = self.config.get("risk_threshold", 0.6)

    def decide(self, goal_ctx: dict) -> dict:
        semantic = goal_ctx.get("semantic") or {}
        intent = semantic.get("intent", "unknown")

        # 從 goal_ctx 找參數（上游可能塞在 logic.exec.params）
        params = {}
        logic = goal_ctx.get("logic") or {}
        if isinstance(logic, dict):
            exec_block = logic.get("exec") or {}
            if isinstance(exec_block, dict):
                params = exec_block.get("params") or {}

        policy = get_intent_policy(intent)

        decision = {
            "intent": intent,
            "approved": True,
            "priority": "normal",
            "reason": "auto-approved (l7 v0.2)",
            "risk_score": 0.1,
            "requires_approval": policy.get("requires_approval", False),
        }

        if params:
            decision["params"] = params

        return decision
