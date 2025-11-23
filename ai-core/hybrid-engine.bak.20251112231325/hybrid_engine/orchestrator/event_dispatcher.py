from hybrid_engine.core.meta import MetaLog
def dispatch(event: dict):
    MetaLog.record("dispatch", event)
    return {"dispatched": True, "type": event.get("type","unknown")}
