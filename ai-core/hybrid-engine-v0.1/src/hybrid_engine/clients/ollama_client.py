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
