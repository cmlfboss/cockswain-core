
import asyncio
from httpx import AsyncClient
from mind_proxy.server import app

async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

# pytest -q
