# /srv/cockswain-core/ai-core/l7/helmsman_core.py

from .context_fusion import ContextFusion
from .intent_goal_mapper import IntentGoalMapper
from .meta_judgment import MetaJudgment
from .orchestrator import Orchestrator
from .self_reflection import SelfReflection
from .dao_gateway import DAOGateway

ALLOWED_CALLERS = {"helmsman-api"}


class HelmsmanCore:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.context_fusion = ContextFusion(self.config.get("context_fusion", {}))
        self.intent_goal = IntentGoalMapper(self.config.get("intent_goal", {}))
        self.meta_judge = MetaJudgment(self.config.get("meta_judgment", {}))
        self.orchestrator = Orchestrator(self.config.get("orchestrator", {}))
        self.reflection = SelfReflection(self.config.get("self_reflection", {}))
        self.dao = DAOGateway(self.config.get("dao_gateway", {}))

    def tick(self, layers_payload: dict) -> dict:
        caller = layers_payload.get("_caller")
        is_trusted = caller in ALLOWED_CALLERS

        steps = layers_payload.get("steps")
        if isinstance(steps, list):
            results = []
            for step in steps:
                results.append(self._run_single(step, is_trusted=is_trusted))
            return {"type": "sequence_result", "results": results}

        return self._run_single(layers_payload, is_trusted=is_trusted)

    def _run_single(self, layers_payload: dict, is_trusted: bool = False) -> dict:
        fused_ctx = self.context_fusion.fuse(layers_payload)
        goal_ctx = self.intent_goal.map(fused_ctx)
        decision = self.meta_judge.decide(goal_ctx)
        if is_trusted:
            decision["is_trusted_caller"] = True
        actions = self.orchestrator.dispatch(decision)
        self.reflection.record(fused_ctx, goal_ctx, decision, actions)
        return {
            "fused_ctx": fused_ctx,
            "goal_ctx": goal_ctx,
            "decision": decision,
            "actions": actions,
        }
