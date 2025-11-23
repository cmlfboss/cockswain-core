#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cockswain Action Runner v1.0

用途：
- 從 workspace/auto_code/meta/actions.json 中讀取 action 定義
- 依 action 名稱執行對應的指令（目前先支援 type = "shell"）

用法範例：
    python3 scripts/run_action.py merge_logs
    python3 scripts/run_action.py merge_logs --today-only
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List


AI_CORE_ROOT = Path("/srv/cockswain-core/ai-core").resolve()
ACTIONS_FILE = AI_CORE_ROOT / "workspace" / "auto_code" / "meta" / "actions.json"


def load_actions() -> dict:
    if not ACTIONS_FILE.exists():
        raise FileNotFoundError(f"找不到 actions 設定檔: {ACTIONS_FILE}")
    with ACTIONS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("actions.json 格式錯誤，頂層必須是物件 {}")
    return data


def run_shell_action(path: str, extra_args: List[str]) -> int:
    """
    執行 shell 類型的 action。
    """
    cmd = [path] + extra_args
    print(f"[action-runner] 執行指令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main(argv: List[str]) -> None:
    if len(argv) < 2:
        print("用法: python3 scripts/run_action.py <action_name> [args...]", file=sys.stderr)
        sys.exit(1)

    action_name = argv[1]
    extra_args = argv[2:]

    actions = load_actions()

    if action_name not in actions:
        print(f"[action-runner] 未找到 action: {action_name}", file=sys.stderr)
        print(f"[action-runner] 可用 actions: {', '.join(actions.keys())}", file=sys.stderr)
        sys.exit(1)

    action = actions[action_name]
    action_type = action.get("type")
    action_path = action.get("path")

    if not action_path:
        print(f"[action-runner] action '{action_name}' 缺少 path 設定", file=sys.stderr)
        sys.exit(1)

    if action_type == "shell":
        code = run_shell_action(action_path, extra_args)
        sys.exit(code)
    else:
        print(f"[action-runner] 尚未支援的 action type: {action_type}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
