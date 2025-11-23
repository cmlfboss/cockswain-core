#!/usr/bin/env python3
# /srv/cockswain-core/ai-core/scripts/run_autocoder.py

import os
import sys

# 把上一層目錄 (/srv/cockswain-core/ai-core) 加進 sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from auto_coder import AutoCoder


def main():
    # 1) 取得使用者需求：優先用命令列參數，沒有就互動輸入
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        try:
            request = input("請輸入自動編程需求：").strip()
        except EOFError:
            request = ""
        if not request:
            print("沒有輸入任何需求，自動編程結束。")
            return

    ac = AutoCoder()
    result = ac.run(request)

    print("=== REQUEST ===")
    parsed = result.get("parsed", {})
    print(parsed.get("raw", request))

    print("=== PARSED ===")
    print(parsed)

    print("=== OUTPUT FILE ===")
    print(result.get("output_file"))

    print("=== PREVIEW (前 400 字) ===")
    preview = result.get("preview", "")
    print(preview[:400])


if __name__ == "__main__":
    main()
