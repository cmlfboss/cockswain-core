#!/usr/bin/env python3
"""
簡單的 AutoEditor 測試／執行入口：

用法：
  1) 新增一份文件：
     python3 scripts/run_auto_editor.py add "內容..." tag1,tag2

  2) 排入一個編輯任務：
     python3 scripts/run_auto_editor.py enqueue DOC_ID rewrite_soft

  3) 執行一次任務 queue：
     python3 scripts/run_auto_editor.py run
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
# 確保可以 import sibling package：knowledge_center
import sys as _sys
_sys.path.insert(0, str(ROOT_DIR))

from knowledge_center import kc_base, auto_editor  # noqa: E402


def usage():
    print("Usage:")
    print("  python3 scripts/run_auto_editor.py add \"內容...\" [tag1,tag2...]")
    print("  python3 scripts/run_auto_editor.py enqueue DOC_ID [operation]")
    print("  python3 scripts/run_auto_editor.py run")
    sys.exit(1)


def main(argv):
    if len(argv) < 2:
        usage()

    cmd = argv[1]
    kc = kc_base.KnowledgeCenter()
    ae = auto_editor.AutoEditor()

    if cmd == "add":
        if len(argv) < 3:
            usage()
        content = argv[2]
        tags = argv[3].split(",") if len(argv) >= 4 else []
        doc_id = kc.add_document(
            content,
            source="run_auto_editor",
            doc_type="note",
            tags=tags,
        )
        print("NEW DOC_ID:", doc_id)
        return

    if cmd == "enqueue":
        if len(argv) < 4:
            usage()
        doc_id = argv[2]
        operation = argv[3]
        task_id = ae.enqueue_task(doc_id, operation)
        print("ENQUEUED TASK_ID:", task_id)
        return

    if cmd == "run":
        ae.run_once()
        print("AUTO_EDITOR RUN DONE")
        return

    usage()


if __name__ == "__main__":
    main(sys.argv)
