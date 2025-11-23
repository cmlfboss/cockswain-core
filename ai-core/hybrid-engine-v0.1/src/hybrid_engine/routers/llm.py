from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, constr
from fastapi.responses import StreamingResponse, JSONResponse
import logging
from hybrid_engine.clients.ollama_client import OllamaClient

log = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])

PromptStr = constr(strip_whitespace=True, min_length=1, max_length=10000)

class CompleteRequest(BaseModel):
    prompt: PromptStr
    system: Optional[str] = Field(default=None, max_length=4000)
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8192)
    stream: bool = False
    keep_alive: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class CompleteResponse(BaseModel):
    model: str
    text: str
    stats: Dict[str, Any]

@router.post("/complete", response_model=CompleteResponse)
async def complete(req: CompleteRequest):
    client = OllamaClient()
    try:
        if not req.stream:
            result = await client.generate(**req.dict())
            return JSONResponse(result)
        async def token_stream():
            try:
                async for token in client.stream_generate(**req.dict()):
                    yield token
            except Exception as e:
                log.exception("stream error: %s", e)
                yield "\n[STREAM_ERROR]\n"
        return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")
    except Exception as e:
        log.exception("complete error: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM backend error: {type(e).__name__}")
    finally:
        await client.close()
