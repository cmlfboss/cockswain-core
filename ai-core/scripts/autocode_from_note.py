#!/usr/bin/env python3

"""
Cockswain Auto Coder v3 - From Note

功能：
- 從指定的 note 檔案讀取自然語言描述
- 呼叫 auto_coder.v3_core.generate_from_text
- 在 workspace/auto_code 底下產生一支 Python 腳本
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from auto_coder.v3_core import generate_from_text  # type: ignore


def main():
    # 預設先用你之前測試用的 note 路徑
    default_note = os.path.join(
        BASE_DIR,
        "knowledge_center",
        "inbox",
        "openai",
        "test_note.txt",
    )

    note_path = sys.argv[1] if len(sys.argv) > 1 else default_note

    if not os.path.isfile(note_path):
        print(f"[autocode-from-note] 找不到 note 檔案：{note_path}")
        sys.exit(1)

    with open(note_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print(f"[autocode-from-note] note 是空的：{note_path}")
        sys.exit(1)

    print(f"[autocode-from-note] 讀取 note：{note_path}")
    print(f"[autocode-from-note] 內容預覽：{text[:80]!r}")

    try:
        path = generate_from_text(text)
    except Exception as e:
        print(f"[autocode-from-note] 產生程式失敗：{e}")
        sys.exit(1)

    print(f"[autocode-from-note] generated script: {path}")
    print(f"[autocode-from-note] 你可以用以下指令測試：")
    print(f"    python3 {path}")


if __name__ == "__main__":
    main()
