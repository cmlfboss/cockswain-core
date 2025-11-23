#!/usr/bin/env python3
"""
Cockswain Helm Watchdog

- 檢查兩位舵手容器是否存在 & 是否在跑
- 若沒在跑 → 嘗試啟動
- 若啟動失敗 → 記錄告警
- 將狀態寫入 /srv/cockswain-core/logs/helm_status.json
- 若 AI Core 有在跑，嘗試呼叫 /helmsman/list-all 做連通測試
"""
import json
import subprocess
import datetime
import os
from typing import Dict, Any

LOG_DIR = "/srv/cockswain-core/logs"
STATUS_FILE = os.path.join(LOG_DIR, "helm_status.json")

# 之後你真的把兩位舵手容器起來，就會用到這兩個名字
HELM_CONTAINERS = [
    "cockswain-helm-main",
    "cockswain-helm-sandbox",
]

AI_CORE_URL = "http://127.0.0.1:8000/helmsman/list-all"


def ts() -> str:
    return datetime.datetime.utcnow().isoformat()


def docker_is_running(name: str) -> bool:
    try:
        out = subprocess.check_output(
            ["sudo", "docker", "inspect", "-f", "{{.State.Running}}", name],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        return out == "true"
    except subprocess.CalledProcessError:
        return False


def docker_start(name: str) -> bool:
    try:
        subprocess.check_output(["sudo", "docker", "start", name], stderr=subprocess.STDOUT, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


def check_ai_core() -> bool:
    try:
        subprocess.check_output(["curl", "-sSf", AI_CORE_URL], stderr=subprocess.STDOUT, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    report: Dict[str, Any] = {
        "ts": ts(),
        "ai_core_ok": False,
        "containers": [],
        "alerts": [],
    }

    # 檢查 AI core
    ai_ok = check_ai_core()
    report["ai_core_ok"] = ai_ok
    if not ai_ok:
        report["alerts"].append("ai_core_unreachable")

    # 檢查每一個舵手容器
    for name in HELM_CONTAINERS:
        running = docker_is_running(name)
        entry = {
            "name": name,
            "running": running,
            "action": None,
        }
        if not running:
            started = docker_start(name)
            entry["action"] = "started" if started else "start_failed"
            if not started:
                report["alerts"].append(f"{name}_start_failed")
        report["containers"].append(entry)

    # 寫出狀態
    with open(STATUS_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report))


if __name__ == "__main__":
    main()
