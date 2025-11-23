# /srv/cockswain-core/ai-core/l7/intent_goal_mapper.py

class IntentGoalMapper:
    """
    v0.1: 不做轉換，直接回傳 fused_ctx
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def map(self, fused_ctx: dict) -> dict:
        return fused_ctx
