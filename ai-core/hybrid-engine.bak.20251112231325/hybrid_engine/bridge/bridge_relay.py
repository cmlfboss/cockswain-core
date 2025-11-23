from hybrid_engine.core.meta import MetaLog

def relay(command: str, payload: dict):
    MetaLog.record("relay", {"command": command, "payload": payload})
    return {"ok": True, "command": command}
