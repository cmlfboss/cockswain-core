from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from hybrid_engine.core.store import add_note, list_notes, search_by_vector

# 這個 router 會掛在 /bridge 底下
router = APIRouter(prefix="/bridge", tags=["bridge"])


# ------------------------------
# model 定義
# ------------------------------
class NoteBody(BaseModel):
    role: str = "user"
    text: str
    meta: Optional[Dict[str, Any]] = None


class AskBody(BaseModel):
    msg: str


# ------------------------------
# /bridge/note : 記一筆 note
# ------------------------------
@router.post("/note")
async def note(body: NoteBody) -> Dict[str, Any]:
    note_id = add_note(body.role, body.text, body.meta or {})
    return {"ok": True, "note_id": note_id}


# ------------------------------
# /bridge/ask : v0.1 測試版
# ------------------------------
@router.post("/ask")
async def ask(body: AskBody) -> Dict[str, Any]:
    """
    v0.1 過渡版：

    - 不啟用真正的 RAG
    - 不一定要呼叫本地 LLM（之後再接 Ollama / 其他微服務）
    - 目前只回一段 echo-style 回覆，確認整條 HTTP 管線正常
    """

    text = body.msg

    # 目前 search_by_vector 會直接回 []
    hits: List[Dict[str, Any]] = search_by_vector([], k=5)

    answer = (
        f"【混合引擎 v0.1 測試回應】已收到訊息：「{text}」。"
        f"目前先確認服務管線正常，RAG 與本地模型之後再啟用。"
    )

    return {
        "ok": True,
        "answer": answer,
        "hits": hits,
    }
