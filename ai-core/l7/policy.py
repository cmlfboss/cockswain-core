# /srv/cockswain-core/ai-core/l7/policy.py

INTENT_POLICY = {
    "record_progress": {"requires_approval": False},
    "check_node_state": {"requires_approval": False},
    "core_status": {"requires_approval": False},
    "sync_docs": {"requires_approval": False},
    "start_core": {"requires_approval": True},
    "approve_intent": {"requires_approval": False},
}


def get_intent_policy(intent: str) -> dict:
    return INTENT_POLICY.get(intent, {"requires_approval": False})
