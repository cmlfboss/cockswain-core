#!/usr/bin/env python3
import sys
from pathlib import Path

# 確保可以 import auto_coder 套件
THIS_FILE = Path(__file__).resolve()
BASE_DIR = THIS_FILE.parents[1]  # /srv/cockswain-core/ai-core
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from auto_coder.orchestrator import run_auto_coder  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法:")
        print('  auto_coder_cli.py "用自然語言描述你想要的程式"')
        return 1

    raw_request = argv[1]
    spec = run_auto_coder(raw_request, created_by="local-cli", source="cli")

    print(f"Task ID : {spec.task_id}")
    print(f"Status  : {spec.status}")
    print(f"Goal    : {spec.goal}")

    print("=== STDOUT ===")
    if spec.exec_stdout:
        print(spec.exec_stdout, end="")

    print("\n=== STDERR ===")
    if spec.exec_stderr:
        print(spec.exec_stderr, end="")

    if spec.error:
        print("\n=== ERROR ===")
        print(spec.error)

    if spec.exec_cwd:
        print("\n=== CODE DIR ===")
        print(spec.exec_cwd)

    return 0 if spec.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
