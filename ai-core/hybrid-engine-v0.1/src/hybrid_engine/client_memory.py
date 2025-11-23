import os
import httpx

MK_URL = os.getenv("MK_URL", "http://127.0.0.1:7781")
MK_TIMEOUT = float(os.getenv("MK_TIMEOUT", "2.0"))

async def append_memory(role: str, content: str, tags=None):
    url = f"{MK_URL.rstrip('/')}/append"
    payload = {"role": role or "system", "content": content, "tags": tags or []}
    try:
        async with httpx.AsyncClient(timeout=MK_TIMEOUT) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return True
    except Exception:
        # 靜默失敗，不阻斷主流程
        return False