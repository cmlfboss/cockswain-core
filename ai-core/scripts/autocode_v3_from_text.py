# /srv/cockswain-core/ai-core/scripts/autocode_v3_from_text.py
#!/usr/bin/env python3

"""
CLI 入口：
舵手 v3 自動編程 - 從一段自然語言描述產生 Python 腳本。

用法：
    python3 scripts/autocode_v3_from_text.py "幫我整理 /srv/cockswain-core/logs 的 log"
或是：
    echo "幫我掃描 log 找 ERROR" | python3 scripts/autocode_v3_from_text.py
"""

import sys
import os

# 讓它可以 import auto_coder.v3_core
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from auto_coder.v3_core import generate_from_text  # type: ignore


def read_input_text() -> str:
    if len(sys.argv) > 1:
        # 直接把所有參數串起來當作一句話
        return " ".join(sys.argv[1:])
    else:
        # 從 stdin 讀
        data = sys.stdin.read()
        return data


def main():
    text = read_input_text().strip()
    if not text:
        print("[autocode-v3] 沒有收到自然語言描述，什麼都生不出來。")
        sys.exit(1)

    try:
        path = generate_from_text(text)
    except Exception as e:
        print(f"[autocode-v3] 產生程式失敗：{e}")
        sys.exit(1)

    print(f"[autocode-v3] generated script: {path}")
    print(f"[autocode-v3] 你可以用以下指令測試：")
    print(f"    python3 {path}")


if __name__ == "__main__":
    main()
