sudo bash -c 'cat <<"EOF" > /srv/cockswain-core/ai-core/l7/intent_goal_mapper.py
class IntentGoalMapper:
    """
    v0.1 極簡版
    現在只是把融合好的 context 原樣丟回去，
    給 helmsman_core 往下跑用。
    未來要做真正的 intent→goal 映射，再改這支就好。
    """
    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def map(self, fused_ctx: dict) -> dict:
        return fused_ctx
EOF'
