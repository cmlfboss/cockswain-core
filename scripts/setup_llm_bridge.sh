#!/usr/bin/env bash
set -euo pipefail

ENGINE_DIR="/srv/cockswain-core/ai-core/hybrid-engine-v0.1/src/hybrid_engine"

echo ">>> 建立核心資料夾"
mkdir -p "$ENGINE_DIR"/{core,clients,routers}

# 1️⃣ config.py
cat > "$ENGINE_DIR/core/config.py" <<'PY'
import os
from pydantic import BaseModel, Field, ValidationError

class LLMConfig(BaseModel):
    base_url: str = Field(default=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434"))
    model: str = Field(default=os.getenv("LLM_MODEL", "llama3.1:8b-instruct-q4_K_M"))
    timeout: float = Field(default=float(os.getenv("LLM_TIMEOUT", "60")))
    max_tokens: int = Field(default=int(os.getenv("LLM_MAX_TOKENS", "1024")))
    keep_alive: str = Field(default=os.getenv("LLM_KEEP_ALIVE", "5m"))

def get_llm_config() -> LLMConfig:
    try:
        return LLMConfig()
    except ValidationError:
        return LLMConfig()
PY

# 2️⃣ ollama_client.py
cat > "$ENGINE_DIR/clients/ollama_client.py" <<'PY'
from typing import AsyncGenerator, Dict, Any, Optional
import httpx, time
from hybrid_engine.core.config import get_llm_config

class OllamaClient:
    def __init__(self):
        self.cfg = get_llm_config()
        self._client = httpx.AsyncClient(base_url=self.cfg.base_url, timeout=self.cfg.timeout)

    async def close(self):
        await self._client.aclose()

    async def generate(self, prompt: str, model: Optional[str] = None, temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None, keep_alive: Optional[str] = None,
                       system: Optional[str] = None, options: Optional[Dict[str, Any]] = None,
                       stream: bool = False) -> Dict[str, Any]:
        payload = {"model": model or self.cfg.model, "prompt": prompt, "keep_alive": keep_alive or self.cfg.keep_alive}
        if system:
            payload["system"] = system
        _opts = options.copy() if options else {}
        if temperature is not None:
            _opts["temperature"] = temperature
        _opts["num_predict"] = max_tokens if max_tokens else self.cfg.max_tokens
        if _opts:
            payload["options"] = _opts

        t0 = time.perf_counter()
        text_chunks, stats = [], {}
        async with self._client.stream("POST", "/api/generate", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line: continue
                try:
                    data = httpx.Response(200, text=line).json()
                except Exception:
                    continue
                if "response" in data:
                    text_chunks.append(data["response"])
                if data.get("done"):
                    stats = {k: data.get(k) for k in ["load_duration","prompt_eval_count","prompt_eval_duration",
                                                      "eval_count","eval_duration","total_duration"]}
                    break
        return {"model": payload["model"], "text": "".join(text_chunks), "stats": {**stats, "latency_s": time.perf_counter()-t0}}

    async def stream_generate(self, prompt: str, model: Optional[str] = None, temperature: Optional[float] = None,
                              max_tokens: Optional[int] = None, keep_alive: Optional[str] = None,
                              system: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        payload = {"model": model or self.cfg.model, "prompt": prompt, "keep_alive": keep_alive or self.cfg.keep_alive}
        if system: payload["system"] = system
        _opts = options.copy() if options else {}
        if temperature is not None: _opts["temperature"] = temperature
        _opts["num_predict"] = max_tokens if max_tokens else self.cfg.max_tokens
        if _opts: payload["options"] = _opts
        async with self._client.stream("POST", "/api/generate", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line: continue
                try:
                    data = httpx.Response(200, text=line).json()
                except Exception:
                    continue
                if token := data.get("response"):
                    yield token
                if data.get("done"): return
PY

# 3️⃣ llm.py
cat > "$ENGINE_DIR/routers/llm.py" <<'PY'
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
PY

echo ">>> 模組檔案建立完成於：$ENGINE_DIR"

# 簡單語法檢查
echo ">>> 執行語法檢查"
python3 -m py_compile "$ENGINE_DIR"/{core,clients,routers}/*.py || true

echo ">>> 重啟 hybrid 引擎服務"
sudo systemctl daemon-reload
sudo systemctl restart cockswain-hybrid-engine

echo ">>> 檢查狀態"
systemctl --no-pager status cockswain-hybrid-engine | head -n 15

echo "✅ 完成！請測試："
echo "curl -s http://127.0.0.1:7790/health"
echo "curl -s http://127.0.0.1:7790/llm/complete -H 'Content-Type: application/json' -d '{\"prompt\":\"台灣夜市簡介\"}' | jq"
