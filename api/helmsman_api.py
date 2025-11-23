import sys
import os
from pathlib import Path
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse

# 把 ai-core 加進來，讓我們能 import l7
sys.path.append("/srv/cockswain-core/ai-core")

app = FastAPI(title="Cockswain Helmsman API", version="0.2")

LOG_DIR = Path("/srv/cockswain-core/logs/api")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "helmsman_api.log"

# 固定金鑰（預設）
HARDCODED_TOKEN = "super-secret-helmsman-token"

# 允許從 .env 覆蓋
BASE_DIR = Path("/srv/cockswain-core")
ENV_PATH = BASE_DIR / ".env"
API_TOKEN = HARDCODED_TOKEN
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("HELMSMAN_TOKEN="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                API_TOKEN = val
                break


def write_log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


@app.post("/ping")
async def ping():
    return JSONResponse(content={"ok": True})


@app.post("/api/v1/helmsman/tick")
async def helmsman_tick(
    request: Request,
    x_helmsman_token: str = Header(default=None, alias="X-Helmsman-Token"),
):
    # 1) 來源 IP 鎖本機
    client_host = request.client.host
    if client_host not in ("127.0.0.1", "::1"):
        write_log(f"DENY remote access from {client_host}")
        raise HTTPException(status_code=403, detail="Forbidden: internal only")

    # 2) token 驗證
    if not x_helmsman_token or x_helmsman_token != API_TOKEN:
        write_log("DENY invalid token")
        raise HTTPException(status_code=401, detail="Unauthorized: invalid token")

    # 3) 取 payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Bad JSON")

    # 4) import L7
    try:
        from l7 import HelmsmanCore  # type: ignore
    except Exception as e:
        write_log(f"IMPORT ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail="L7 import failed")

    # 5) 標記呼叫來源，給 L7 判斷是高權限通道
    payload["_caller"] = "helmsman-api"

    core = HelmsmanCore({})

    try:
        result = core.tick(payload)
    except Exception as e:
        write_log(f"tick error: {repr(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return JSONResponse(content=result)
