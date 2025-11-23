
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from .core.config import get_settings
from .utils.logging import setup_logging
from .routes.http import router as http_router

settings = get_settings()
log = setup_logging(settings.log_level)

REQ_COUNTER = Counter("mind_proxy_requests_total", "Total HTTP requests", ["path", "method", "code"])

app = FastAPI(title="mind-proxy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")] if settings.allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def prom_mw(request, call_next):
    response = await call_next(request)
    try:
        REQ_COUNTER.labels(path=request.url.path, method=request.method, code=str(response.status_code)).inc()
    except Exception:
        pass
    return response

app.include_router(http_router)

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

def run():
    log.info("starting", host=settings.host, port=settings.port, upstream=settings.upstream_base_url)
    uvicorn.run("mind_proxy.server:app", host=settings.host, port=settings.port, reload=False, workers=1)
