#!/usr/bin/env python3
"""
KC AutoCode Bridge v2

用途：
- 從 Knowledge Center / 檔案 取得規格文字
- 統一丟給 auto_coder.generator_v2 處理
- 將產出的檔案路徑回報到 stdout（給你看、給之後 L7 用）

目前簡化版：
- mode=from_doc: 會從預設的 docs 目錄載入 {doc_id}.md 或 {doc_id}.txt
- 之後你要改成用 KC API 抓資料，只要改 get_spec_from_doc_id() 就好
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 調整 path，讓我們可以 import auto_coder
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from auto_coder.generator_v2 import AutoCodeTask, generate_code_file  # type: ignore


KC_DOCS_DIR = BASE_DIR / "knowledge-center" / "docs"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_spec_from_doc_id(doc_id: str) -> str:
    """
    過渡版實作：
    - 嘗試從 knowledge-center/docs/{doc_id}.md
    - 若沒有，再試 {doc_id}.txt
    - 若兩者都沒有，就噴錯

    之後你若改成用 DB / API，只要改這裡即可。
    """
    candidates = [
        KC_DOCS_DIR / f"{doc_id}.md",
        KC_DOCS_DIR / f"{doc_id}.txt",
    ]

    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"找不到對應 doc 檔案：{doc_id}（預期路徑之一：{', '.join(str(c) for c in candidates)}）"
    )


def run_from_doc(doc_id: str) -> int:
    print("=== MODE === from_doc")
    print(f"=== DOC_ID === {doc_id}")

    try:
        spec_text = get_spec_from_doc_id(doc_id)
    except FileNotFoundError as exc:
        eprint(f"[kc_autocode_bridge] ERROR: {exc}")
        return 1

    task = AutoCodeTask(
        task_id=f"doc-{doc_id}",
        source="doc",
        doc_id=doc_id,
        title=f"KC Doc {doc_id}",
        hint="來源：KC 規格文件（from_doc）。請依內容產出對應程式碼。",
    )

    out_path = generate_code_file(task, spec_text)
    print("=== OUTPUT FILE ===")
    print(out_path)
    print("=== PREVIEW (前 400 字) ===")

    try:
        preview = out_path.read_text(encoding="utf-8")[:400]
        print(preview)
    except Exception as exc:  # noqa: BLE001
        eprint(f"[kc_autocode_bridge] WARNING: 無法讀取預覽：{exc}")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        eprint("用法：kc_autocode_bridge.py from_doc <DOC_ID>")
        return 1

    mode = argv[0]

    if mode == "from_doc":
        if len(argv) < 2:
            eprint("用法：kc_autocode_bridge.py from_doc <DOC_ID>")
            return 1
        doc_id = argv[1]
        return run_from_doc(doc_id)

    eprint(f"未知的 mode：{mode}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
