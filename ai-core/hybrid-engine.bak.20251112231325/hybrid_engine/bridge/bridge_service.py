import time, json, threading
from pathlib import Path
from hybrid_engine.core.meta import MetaLog

HEALTH_PATH = Path("/srv/cockswain-core/health")
HEALTH_PATH.mkdir(parents=True, exist_ok=True)

def write_health(status: dict):
    (HEALTH_PATH / "hybrid_engine.json").write_text(json.dumps(status, ensure_ascii=False), encoding="utf-8")

def bridge_loop():
    while True:
        status = {
            "uptime": time.time(),
            "status": "running",
            "source": "bridge_service"
        }
        write_health(status)
        MetaLog.record("bridge_tick", status)
        time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=bridge_loop, daemon=False)
    t.start()
    t.join()
