
from fastapi import APIRouter, Request, HTTPException
from .schemas import ChatRequest, ProxyResponse
from ..core.config import get_settings
from ..adapters.http_upstream import HttpUpstream
from ..utils.rate_limit import MemoryRateLimiter
from ..utils.circuit_breaker import CircuitBreaker
import uuid

router = APIRouter()
settings = get_settings()
rate = MemoryRateLimiter(settings.rate_limit_tokens, settings.rate_limit_refill_per_sec)
breaker = CircuitBreaker(settings.cb_fail_threshold, settings.cb_cooldown_seconds)
upstream = HttpUpstream(settings.upstream_base_url, settings.upstream_timeout_seconds)

@router.post("/v1/proxy/chat", response_model=ProxyResponse)
async def proxy_chat(req: Request, body: ChatRequest):
    rid = req.headers.get("x-request-id") or str(uuid.uuid4())
    ip = req.client.host if req.client else "unknown"
    if settings.rate_limit_enabled and not rate.check(ip):
        raise HTTPException(status_code=429, detail="rate limited")

    if settings.cb_enabled and not breaker.allow():
        raise HTTPException(status_code=503, detail="upstream temporarily unavailable")

    try:
        resp = await upstream.chat(body.model_dump())
        if 200 <= resp.status < 500:
            breaker.record_success()
        else:
            breaker.record_failure()
        return ProxyResponse(status=resp.status, body=resp.text, upstream=settings.upstream_base_url, request_id=rid)
    except Exception as e:
        breaker.record_failure()
        raise HTTPException(status_code=502, detail=f"upstream error: {e}")

@router.get("/health")
async def health():
    return {"status":"ok"}

