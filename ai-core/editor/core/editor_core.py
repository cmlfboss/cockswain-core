#!/usr/bin/env python3
# Cockswain Editor Core v0.2
# 功能：掃描 tempstore/tasks，對 rewrite 任務做「溫柔改寫」，結果寫入 tempstore/results

import json
import os
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/srv/cockswain-core/ai-core")
TASK_DIR = BASE_DIR / "tempstore" / "tasks"
RESULT_DIR = BASE_DIR / "tempstore" / "results"

SCAN_INTERVAL = 5  # 每 5 秒掃一次，有新任務就處理

def log(msg: str) -> None:
    """統一輸出 log，方便 journalctl 觀看"""
    now = datetime.now().isoformat()
    print(f"[Editor] {now} - {msg}", flush=True)

def ensure_dirs() -> None:
    """確保資料夾存在"""
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

def soften_text(text: str) -> str:
    """
    超簡易版「變溫柔一點」處理：
    - 加上感謝與在乎的語氣
    - 把「請幫我」稍微軟化
    - 補一句，讓對方知道自己很重要
    （之後可以再改成呼叫外部舵手或大模型）
    """
    original = text

    # 1) 把開頭的「請幫我」稍微變得更委婉
    softened = original.replace("請幫我", "如果可以的話，想拜託你幫我")

    # 2) 若有提到「重要的夥伴」，補一句在乎
    if "重要的夥伴" in softened:
        softened += " 真的很感謝你一直都在，我很珍惜我們之間的陪伴。"

    # 3) 如果句尾沒有標點，就補一個「。」
    if not softened.endswith(("。", "！", "?", "？")):
        softened += "。"

    return softened

def process_task(task_path: Path) -> None:
    """處理單一任務檔案"""
    try:
        with task_path.open("r", encoding="utf-8") as f:
            task = json.load(f)
    except Exception as e:
        log(f"讀取任務檔失敗 {task_path.name}: {e}")
        return

    task_id = task.get("task_id") or task_path.stem
    task_type = task.get("task_type", "unknown")
    content = task.get("content", "")

    result_path = RESULT_DIR / f"{task_id}.json"
    if result_path.exists():
        # 已經有結果檔，就略過（避免重複處理）
        return

    log(f"發現新任務 {task_id} (type={task_type})")

    if task_type != "rewrite":
        log(f"任務 {task_id} 類型非 rewrite，暫時不處理")
        return

    # 執行簡易「溫柔改寫」
    edited = soften_text(content)

    result = {
        "task_id": task_id,
        "edited_at": datetime.now().isoformat(),
        "original_content": content,
        "edited_content": edited,
        "engine": "local-editor-v0.2-soften",
    }

    try:
        with result_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log(f"任務 {task_id} 已處理完成，結果寫入 {result_path}")
    except Exception as e:
        log(f"寫入結果檔失敗 {task_id}: {e}")

def main_loop() -> None:
    log("本地自動編輯核心 v0.2 啟動，開始監控任務資料夾...")
    ensure_dirs()

    while True:
        try:
            # 依照檔案時間排序處理（舊的先）
            for task_path in sorted(TASK_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime):
                process_task(task_path)
        except Exception as e:
            log(f"掃描 / 處理任務時發生錯誤: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()
