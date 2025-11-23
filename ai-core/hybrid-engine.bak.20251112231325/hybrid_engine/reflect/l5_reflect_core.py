from hybrid_engine.core.meta import MetaLog
def reflect(event: dict):
    MetaLog.record("reflect", {"event": event})
    return {"noted": True}
