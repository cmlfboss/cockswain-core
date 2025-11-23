from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import httpx, json
from ..core.config import get_llm_config

router = APIRouter(prefix="/llm", tags=["llm"])

@router.post("/stream")
async def llm_stream(body: dict):
    cfg = get_llm_config()
    payload = {
        "model": body.get("model", cfg.model),
        "prompt": body["prompt"],
        "keep_alive": cfg.keep_alive,
        "options": body.get("options", {"temperature":0.2, "num_predict":512}),
        "stream": True
    }

    async def gen():
        async with httpx.AsyncClient(timeout=cfg.timeout) as client:
            async with client.stream("POST", f"{cfg.base_url}/api/generate", json=payload) as r:
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    # Ollama 串流每行是 JSON；這裡只挑出 text/response 部分，以 NDJSON 回傳
                    try:
                        data = json.loads(line)
                        chunk = data.get("response") or data.get("message", {}).get("content") or ""
                        if chunk:
                            yield json.dumps({"text": chunk}, ensure_ascii=False) + "\n"
                    except json.JSONDecodeError:
                        # 保底直接透傳原始行
                        yield line + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")
