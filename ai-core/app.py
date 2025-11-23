from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import os
import pathlib
import shutil
import pymysql

# === 新增導入 Helmsman 模組 ===
from api import helmsman

# ===== app 定義 =====
app = FastAPI(
    title="Cockswain Local AI Core",
    version="0.5.3",
    description="Cockswain 母機 AI Core 模組 (含 Helmsman 統合查詢 API)"
)

# 掛載 Helmsman Router
app.include_router(helmsman.router)

# ===== models =====
class InferReq(BaseModel):
    prompt: str

class IngestReq(BaseModel):
    path: str | None = None
    content: str | None = None
    title: str | None = None
    tags: list[str] | None = None

# ===== helpers =====
def get_db_conn(dbname: str):
    return pymysql.connect(
        host=os.getenv("DB_HOST", "cockswain-mysql"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "cockswain_core"),
        password=os.getenv("DB_PASSWORD", "changeme"),
        database=dbname,
        cursorclass=pymysql.cursors.DictCursor
    )

# ===== endpoints =====

@app.get("/")
def root():
    return {"status": "ok", "service": "cockswain-ai-core"}

@app.post("/infer")
def infer(req: InferReq):
    # 假設這裡是 AI 推論邏輯（目前用假回傳）
    return {"ok": True, "prompt": req.prompt, "result": f"Echo: {req.prompt}"}

@app.post("/ingest")
def ingest(req: IngestReq):
    """手動匯入資料內容（可存入 Meilisearch 或文件系統）"""
    base_dir = pathlib.Path("/srv/cockswain-core/docs/manual_ingest")
    base_dir.mkdir(parents=True, exist_ok=True)
    file_name = req.title or "untitled.txt"
    target_path = base_dir / file_name

    with open(target_path, "w") as f:
        f.write(req.content or "")
    return {"ok": True, "saved_to": str(target_path)}

@app.get("/health")
def health():
    """快速健康檢查"""
    return {"status": "alive"}

# ===== 可選：範例資料查詢 =====
@app.get("/db-test")
def db_test():
    """快速測試資料庫連線（可刪）"""
    try:
        conn = get_db_conn("cockswain")
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tables = [row[f"Tables_in_cockswain"] for row in cur.fetchall()]
        conn.close()
        return {"ok": True, "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
