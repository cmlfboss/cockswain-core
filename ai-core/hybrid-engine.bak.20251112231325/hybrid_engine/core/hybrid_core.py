import os, asyncio, time, signal
from .meta import log_meta
from .arbiter_gateway import create_decision

TICK_SECONDS = float(os.getenv("HYBRID_TICK", "3"))

async def run_once():
    # 模擬三個 job
    for job in (0, 1, 2):
        d = create_decision("execute", {"job": job, "ts": time.time()})
        log_meta("decision", d)
        log_meta("task_start", {"decision_id": d["decision_id"], "payload": d["payload"]})
        await asyncio.sleep(0.2)
        log_meta("task_end", {"decision_id": d["decision_id"], "result": "ok"})

async def main():
    log_meta("boot", {"status": "starting"})
    stop = asyncio.Event()

    def _stop(*_):
        try:
            stop.set()
        except Exception:
            pass

    try:
        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)
    except Exception:
        pass

    while not stop.is_set():
        await run_once()
        try:
            await asyncio.wait_for(stop.wait(), timeout=TICK_SECONDS)
        except asyncio.TimeoutError:
            pass

    log_meta("shutdown", {"status": "stopped"})

if __name__ == "__main__":
    asyncio.run(main())
