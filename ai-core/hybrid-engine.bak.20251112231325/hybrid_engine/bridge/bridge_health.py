import os, shutil, time
from hybrid_engine.core.meta import MetaLog

def _mem_percent_fallback():
    try:
        import psutil
        return psutil.virtual_memory().percent
    except Exception:
        return 0.0

def health_snapshot():
    return {
        "mem": _mem_percent_fallback(),
        "disk": shutil.disk_usage("/")._asdict(),
        "ts": time.time()
    }

def auto_repair():
    snap = health_snapshot()
    MetaLog.record("health", snap)
    if snap["mem"] > 90:
        os.system("systemctl restart cockswain-hybrid.service")
