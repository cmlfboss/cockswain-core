from fastapi import FastAPI, Request
import json, os, datetime

app = FastAPI()
LOG_PATH = "/srv/cockswain-core/logs/tests"
os.makedirs(LOG_PATH, exist_ok=True)

@app.post("/api/store")
async def store_data(req: Request):
    data = await req.json()
    filename = f"test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(LOG_PATH, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "saved_to": filepath}

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.datetime.now().isoformat()}
