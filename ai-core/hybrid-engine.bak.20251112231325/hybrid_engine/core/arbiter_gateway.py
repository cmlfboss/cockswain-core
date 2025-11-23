import uuid
import datetime
import json
from .meta import MetaLog

def _hash_payload(payload) -> int:
    try:
        return hash(json.dumps(payload, sort_keys=True))
    except Exception:
        return hash(str(payload))

def create_decision(action: str, payload: dict, author: str = "system") -> dict:
    decision = {
        "decision_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "action": action,
        "payload": payload,
        "author": author,
        "proof": _hash_payload(payload),
    }
    MetaLog.record("decision", decision)
    return decision

def verify_proof(decision: dict) -> bool:
    expect = _hash_payload(decision.get("payload", {}))
    return expect == decision.get("proof")
