from fastapi import APIRouter
import httpx
from typing import List, Literal, TypedDict
from ..core.config import get_llm_config

class Msg(TypedDict):
    role: Literal["system","user","assistant"]
    content: str

router = APIRouter(prefix="/llm", tags=["llm"])

def fold_messages(msgs: List[Msg]) -> str:
    tags = {"system":"[SYS]", "user":"[USER]", "assistant":"[ASSIST]"}
    return "\n".join(f"{tags[m['role']]} {m['content']}" for m in msgs)

@router.post("/chat")
async def chat(body: dict):
    cfg = get_llm_config()
    msgs: List[Msg] = body["messages"]
    payload = {
        "model": body.get("model", cfg.model),
        "prompt": fold_messages(msgs),
        "keep_alive": cfg.keep_alive,
        "options": body.get("options", {"temperature":0.2, "num_predict":512})
    }
    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        r = await client.post(f"{cfg.base_url}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        return {"model": payload["model"], "text": data.get("response", data)}
