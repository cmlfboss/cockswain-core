from fastapi import FastAPI
try:
    from .routes import app as _app  # 期望的正常路徑
except Exception as e:
    # 保命：routes 掛了也先把服務撐起來，方便打 /metrics /health 除錯
    _app = FastAPI(title="Cockswain Hybrid Engine (shim)", version="0.1.0")
    @_app.get("/health")
    def _health(): return {"status":"degraded", "reason": str(e)}

app = _app
