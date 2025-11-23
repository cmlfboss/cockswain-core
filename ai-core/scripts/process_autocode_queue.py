#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cockswain Autocode Queue Worker v0.1

功能：
- 掃描 tempstore/tasks/*.json
- 找出 status = "queued" 的任務
- 逐一呼叫：python3 scripts/run_action.py autocode_from_doc <doc_id>
- 從輸出中解析 OUTPUT FILE 路徑
- 回寫任務 JSON：更新 status / generated_at / generated_output_file
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


SCRIPT_PATH = Path(__file__).resolve()
AI_CORE_ROOT = SCRIPT_PATH.parent.parent  # /srv/cockswain-core/ai-core
TEMP_TASK_DIR = AI_CORE_ROOT / "tempstore" / "tasks"
RUN_ACTION = AI_CORE_ROOT / "scripts" / "run_action.py"
LOG_DIR = AI_CORE_ROOT.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_LOG = LOG_DIR / "autocode_queue.log"


def now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def write_log(message: str) -> None:
    line = f"[{now_iso()}] {message}\n"
    if QUEUE_LOG.exists():
        old = QUEUE_LOG.read_text(encoding="utf-8")
    else:
        old = ""
    QUEUE_LOG.write_text(old + line, encoding="utf-8")


def load_task_files() -> List[Path]:
    if not TEMP_TASK_DIR.exists():
        return []
    return sorted(TEMP_TASK_DIR.glob("*.json"))


def load_task(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_task(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_doc_id_from_filename(path: Path) -> str:
    # 檔名格式：<doc_id>.json
    return path.stem


def parse_output_file(stdout: str) -> Optional[str]:
    """
    從 generator 的 stdout 中找出 '=== OUTPUT FILE ===' 那一行。
    期待格式：
        === OUTPUT FILE === /srv/.../xxxxx.py
    """
    prefix = "=== OUTPUT FILE ==="
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            # 拿掉前綴，剩下就是路徑
            return line[len(prefix):].strip()
    return None


def process_task(path: Path, dry_run: bool = False) -> None:
    doc_id = extract_doc_id_from_filename(path)
    task = load_task(path)

    status = task.get("status", "unknown")
    task_type = task.get("task_type", "unknown")

    if status != "queued":
        print(f"[queue] skip (status={status}) {doc_id}")
        return

    print(f"[queue] processing doc_id={doc_id} (task_type={task_type})")

    if dry_run:
        print(f"[queue] DRY-RUN 不實際呼叫 autocode_from_doc，只顯示資訊")
        return

    # 呼叫 run_action
    cmd = [
        sys.executable,
        str(RUN_ACTION),
        "autocode_from_doc",
        doc_id,
    ]

    write_log(f"run {cmd}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        print(f"[queue] autocode_from_doc 失敗 (returncode={result.returncode}) doc_id={doc_id}")
        write_log(f"autocode_from_doc FAILED doc_id={doc_id} code={result.returncode}")
        return

    output_file = parse_output_file(stdout) or ""
    print(f"[queue] parsed output_file={output_file!r}")

    # 更新 task 狀態
    task["status"] = "generated"
    task["generated_at"] = now_iso()
    if output_file:
        task["generated_output_file"] = output_file
    task.setdefault("history", [])
    task["history"].append(
        {
            "event": "autocode_generated",
            "at": now_iso(),
            "output_file": output_file,
            "worker": "process_autocode_queue.py",
        }
    )

    save_task(path, task)
    write_log(f"task_updated doc_id={doc_id} output_file={output_file}")


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser(
        description="Cockswain Autocode Queue Worker v0.1"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只顯示將處理哪些任務，不實際呼叫 autocode",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多處理多少筆（0 = 不限制）",
    )

    args = parser.parse_args(argv[1:])

    task_files = load_task_files()
    if not task_files:
        print(f"[queue] 沒有找到任何任務檔案於 {TEMP_TASK_DIR}")
        return

    print(f"[queue] 掃描到 {len(task_files)} 個任務檔案")
    count = 0

    for path in task_files:
        task = load_task(path)
        if task.get("status", "unknown") != "queued":
            continue

        process_task(path, dry_run=args.dry_run)
        count += 1

        if args.limit and count >= args.limit:
            print(f"[queue] 已達處理上限 limit={args.limit}，停止。")
            break

    if count == 0:
        print("[queue] 沒有符合條件（status=queued）的任務。")
    else:
        print(f"[queue] 本次共處理 {count} 個任務。")


if __name__ == "__main__":
    main(sys.argv)
