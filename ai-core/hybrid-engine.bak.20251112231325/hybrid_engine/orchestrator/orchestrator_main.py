import asyncio
from hybrid_engine.core.meta import MetaLog
from hybrid_engine.bridge.bridge_relay import relay

async def orchestrate():
    MetaLog.record("orchestrate", {"phase": "start"})
    relay("ping", {"hello": "world"})
    await asyncio.sleep(0.1)
    MetaLog.record("orchestrate", {"phase": "end"})

if __name__ == "__main__":
    asyncio.run(orchestrate())
