
import httpx
from pydantic import BaseModel

class UpstreamResponse(BaseModel):
    status: int
    text: str

class HttpUpstream:
    def __init__(self, base_url: str, timeout: float = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def close(self):
        await self.client.aclose()

    async def chat(self, payload: dict) -> UpstreamResponse:
        # Generic forwarding to /chat (POST)
        r = await self.client.post("/chat", json=payload)
        return UpstreamResponse(status=r.status_code, text=r.text)
