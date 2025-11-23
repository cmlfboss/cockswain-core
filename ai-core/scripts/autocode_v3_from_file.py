#!/usr/bin/env python3
"""
從文字檔讀取任務內容，丟給 Cockswain Auto Coder v3 產生程式。
"""

import sys
from pathlib import Path

# 把 ai-core 根目錄加進 sys.path，讓 auto_coder 可以被 import 到
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from auto_coder.v3_core import run_autocode_v3


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: scripts/autocode_v3_from_file.py <任務檔路徑> [workspace_dir]")
        sys.exit(1)

    task_file = Path(sys.argv[1])
    if not task_file.is_file():
        print(f"找不到任務檔案: {task_file}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        workspace_dir = Path(sys.argv[2])
    else:
        workspace_dir = BASE_DIR / "workspace" / "auto_code"

    task_text = task_file.read_text(encoding="utf-8")
    artifact = run_autocode_v3(task_text, workspace_dir)

    print("=== Auto Coder v3 結果 ===")
    print(f"任務檔：{task_file}")
    print(f"輸出檔：{artifact.file_path}")
    print(f"語法驗證：{'通過' if artifact.validated else '失敗'}")
    if artifact.validation_log:
        print("--- 驗證訊息 ---")
        print(artifact.validation_log)


if __name__ == "__main__":
    main()
