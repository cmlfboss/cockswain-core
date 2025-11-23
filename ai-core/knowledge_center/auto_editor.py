import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from . import kc_base


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, "tasks")
EDITS_DIR = os.path.join(BASE_DIR, "edits")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def _ensure_dirs():
    for d in (TASKS_DIR, EDITS_DIR, LOGS_DIR):
        os.makedirs(d, exist_ok=True)


class AutoEditor:
    def __init__(self):
        _ensure_dirs()
        self.kc = kc_base.KnowledgeCenter()

    def _task_queue_path(self) -> str:
        return os.path.join(TASKS_DIR, "edit_queue.jsonl")

    def enqueue_task(
        self,
        doc_id: str,
        operation: str = "rewrite_soft",
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "doc_id": doc_id,
            "operation": operation,
            "extra": extra or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        qpath = self._task_queue_path()
        with open(qpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

        return task_id

    def _iter_tasks(self):
        qpath = self._task_queue_path()
        if not os.path.exists(qpath):
            return

        with open(qpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    def _edit_engine(self, content: str, operation: str, extra: Dict[str, Any]) -> str:
        """
        目前先做三種 demo：
        - rewrite_soft：溫柔改寫（現在只是加個標記）
        - summarize：簡單截斷前 N 行
        - cleanup：把每行右邊多餘空白去掉
        """
        if operation == "summarize":
            max_lines = int(extra.get("max_lines", 5))
            lines = content.splitlines()
            head = "\n".join(lines[:max_lines])
            return f"[summarize v0.1]\n{head}\n...\n（後略）"

        if operation == "cleanup":
            cleaned = "\n".join(line.rstrip() for line in content.splitlines())
            return f"[cleanup v0.1]\n{cleaned}"

        # 預設：rewrite_soft
        return f"[rewrite_soft v0.1]\n{content}"

    def _edit_once(self, task: Dict[str, Any]) -> Optional[str]:
        doc_id = task.get("doc_id")
        if not doc_id:
            return None

        doc = self.kc.get_document(doc_id)
        if not doc:
            return None

        content = doc["content"]
        op = task.get("operation", "rewrite_soft")
        extra = task.get("extra") or {}

        result = self._edit_engine(content, op, extra)

        out_id = f"{doc_id}__{task['task_id']}"
        out_path = os.path.join(EDITS_DIR, f"{out_id}.txt")
        meta_path = os.path.join(EDITS_DIR, f"{out_id}.meta.json")

        meta = {
            "task_id": task["task_id"],
            "doc_id": doc_id,
            "operation": op,
            "extra": extra,
            "created_at": task.get("created_at"),
            "edited_at": datetime.utcnow().isoformat() + "Z",
        }

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        self._log(f"[ok] edited doc_id={doc_id} task_id={task['task_id']} -> {out_path}")
        return out_path

    def _log(self, msg: str):
        log_path = os.path.join(LOGS_DIR, "auto_editor.log")
        ts = datetime.utcnow().isoformat() + "Z"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")

    def run_once(self):
        _ensure_dirs()
        qpath = self._task_queue_path()
        tasks = list(self._iter_tasks() or [])

        # 簡單實作：跑完一次 queue 之後就清空檔案
        if os.path.exists(qpath):
            os.remove(qpath)

        if not tasks:
            self._log("[info] no tasks in queue")
            return

        self._log(f"[info] processing {len(tasks)} tasks...")
        for t in tasks:
            try:
                self._edit_once(t)
            except Exception as e:
                self._log(f"[error] task_id={t.get('task_id')} error={e!r}")
