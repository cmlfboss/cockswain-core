from fastapi import FastAPI
from typing import Optional, List
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi.responses import Response

app = FastAPI(title="Cockswain Hybrid Engine", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# 掛載各功能路由（若模組不存在，忽略即可）
def _try_include(path, obj):
    try:
        app.include_router(obj)
    except Exception:
        pass

try:
    from hybrid_engine.routers.llm import router as llm_router
    _try_include("llm", llm_router)
except Exception:
    pass

try:
    from hybrid_engine.routers.llm_stream import router as llm_stream_router
    _try_include("llm_stream", llm_stream_router)
except Exception:
    pass

try:
    from hybrid_engine.routers.embeddings import router as emb_router
    _try_include("embeddings", emb_router)
except Exception:
    pass

try:
    from hybrid_engine.routers.llm_chat import router as llm_chat_router
    _try_include("llm_chat", llm_chat_router)
except Exception:
    pass

try:
    from hybrid_engine.routers.bridge import router as bridge_router
    _try_include("bridge", bridge_router)
except Exception:
    pass
