from fastapi import APIRouter
import httpx
from ..core.config import get_llm_config

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

@router.post("")
async def embed(body: dict):
    text = body["text"]
    model = body.get("model", "nomic-embed-text")
    cfg = get_llm_config()
    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        r = await client.post(f"{cfg.base_url}/api/embeddings", json={"model": model, "prompt": text})
        r.raise_for_status()
        return r.json()
