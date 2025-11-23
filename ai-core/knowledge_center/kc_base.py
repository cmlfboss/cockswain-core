import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
EDITS_DIR = os.path.join(BASE_DIR, "edits")
TASKS_DIR = os.path.join(BASE_DIR, "tasks")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def _ensure_dirs():
    for d in (RAW_DIR, PROCESSED_DIR, EDITS_DIR, TASKS_DIR, LOGS_DIR):
        os.makedirs(d, exist_ok=True)


class KnowledgeCenter:
    """
    Knowledge Center v0.1

    功能：
    - 接收原始文件（raw）
    - 儲存 metadata（來源、類型、時間戳）
    - 之後可被「自動化編輯」流程取用
    """

    def __init__(self):
        _ensure_dirs()

    def _doc_path(self, doc_id: str) -> str:
        return os.path.join(RAW_DIR, f"{doc_id}.txt")

    def _meta_path(self, doc_id: str) -> str:
        return os.path.join(RAW_DIR, f"{doc_id}.meta.json")

    def add_document(
        self,
        content: str,
        *,
        source: str = "manual",
        doc_type: str = "note",
        tags: Optional[list] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        新增一筆文件，回傳 doc_id
        """
        _ensure_dirs()
        doc_id = str(uuid.uuid4())

        meta: Dict[str, Any] = {
            "doc_id": doc_id,
            "source": source,
            "doc_type": doc_type,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        if extra_meta:
            meta.update(extra_meta)

        with open(self._doc_path(doc_id), "w", encoding="utf-8") as f:
            f.write(content)

        with open(self._meta_path(doc_id), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return doc_id

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        讀取文件與 metadata
        """
        content_path = self._doc_path(doc_id)
        meta_path = self._meta_path(doc_id)

        if not os.path.exists(content_path) or not os.path.exists(meta_path):
            return None

        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        return {
            "meta": meta,
            "content": content,
        }

    def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出最近的文件（依檔案時間排序）
        """
        _ensure_dirs()
        files = [
            f for f in os.listdir(RAW_DIR)
            if f.endswith(".meta.json")
        ]
        files.sort(
            key=lambda name: os.path.getmtime(os.path.join(RAW_DIR, name)),
            reverse=True,
        )

        docs = []
        for name in files[:limit]:
            doc_id = name.replace(".meta.json", "")
            doc = self.get_document(doc_id)
            if doc:
                docs.append(doc)
        return docs
