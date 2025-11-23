import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .l1_processor import normalize_input
from .l2_classifier import classify_task
from .l3_intent import build_intent


TASK_ROOT = Path("/srv/cockswain-core/ai-core/tasks")
INBOX_DIR = TASK_ROOT / "inbox"
PROCESSING_DIR = TASK_ROOT / "processing"
DONE_DIR = TASK_ROOT / "done"
FAILED_DIR = TASK_ROOT / "failed"


def ensure_dirs() -> None:
    for p in [INBOX_DIR, PROCESSING_DIR, DONE_DIR, FAILED_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def load_task(task_path: Path) -> Dict[str, Any]:
    with task_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_result(task: Dict[str, Any], result: Dict[str, Any], dst_dir: Path) -> None:
    task_id = task.get("task_id") or f"no-id-{datetime.utcnow().timestamp()}"
    out_path = dst_dir / f"{task_id}.result.json"
    payload = {
        "task": task,
        "result": result,
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def execute_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    真正執行動作的地方。
    - V3 最小版：只實作 list-files（列出檔案），其他一律回傳 not-implemented。
    """
    intent = intent_data.get("intent", "none")
    params = intent_data.get("params", {})

    if intent == "list-files":
        path = params.get("path", "/home/cocksmain")
        p = Path(path)
        if not p.exists():
            return {
                "status": "error",
                "message": f"path not found: {path}",
            }
        entries = sorted([str(child) for child in p.iterdir()])
        return {
            "status": "ok",
            "action": "list-files",
            "path": path,
            "entries": entries,
        }

    # 其他 intent 先標記為未實作
    return {
        "status": "not-implemented",
        "intent": intent,
    }


def process_one_task(task_path: Path) -> None:
    ensure_dirs()

    # 移到 processing，避免被重複讀
    processing_path = PROCESSING_DIR / task_path.name
    shutil.move(str(task_path), str(processing_path))

    try:
        task = load_task(processing_path)
        text = task.get("payload", {}).get("input", "")
        source = task.get("source", "unknown")

        l1 = normalize_input(text, source=source)
        l2 = classify_task(l1)
        l3 = build_intent(l1, l2)

        result = execute_intent(l3)
        save_result(task, result, DONE_DIR)

        # 處理完就刪掉 processing 中的原始任務
        processing_path.unlink(missing_ok=True)
    except Exception as e:  # noqa: BLE001
        save_result({"task_path": str(processing_path)}, {"status": "error", "error": str(e)}, FAILED_DIR)


def find_next_task() -> Path | None:
    ensure_dirs()
    candidates = sorted(INBOX_DIR.glob("*.json"))
    return candidates[0] if candidates else None
