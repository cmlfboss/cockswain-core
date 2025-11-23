#!/usr/bin/env python3
import os
import time
import yaml
import json
import threading
import requests

# 路徑設定
MASTER_PATH = "/srv/cockswain-core/ai-core/engines.master.yaml"
STATUS_DIR = "/srv/cockswain-core/ai-core/status"
STATUS_PATH = os.path.join(STATUS_DIR, "health.json")

# 週期
HEALTH_INTERVAL = 15  # 秒

# 確保目錄存在
os.makedirs(STATUS_DIR, exist_ok=True)


def load_engines() -> dict:
    """讀取 engines.master.yaml 變成 dict"""
    try:
        with open(MASTER_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print("[L7] load error:", e)
        return {}

    engines = {}
    for item in data.get("engines", []):
        eid = item.get("engine_id")
        if not eid:
            continue
        # 一開始先標成不健康，後面 health loop 會更新
        item["__healthy"] = False
        engines[eid] = item

    print(f"[L7] loaded {len(engines)} engines")
    return engines


def write_status(engines: dict):
    """把目前引擎狀態寫到 health.json"""
    data = {"engines": {}}
    for eid, e in engines.items():
        data["engines"][eid] = {
            "name": e.get("engine_name"),
            "enabled": e.get("enabled", False),
            "healthy": e.get("__healthy", False),
        }

    try:
        with open(STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print("[L7] write_status error:", ex)


def health_loop(engines: dict):
    """定期打每一個 engine 的 health endpoint"""
    while True:
        for eid, e in engines.items():
            if not e.get("enabled", False):
                e["__healthy"] = False
                continue

            hc = e.get("healthcheck", {})
            url = hc.get("endpoint")
            if not url:
                # 沒寫 health 就當作健康
                e["__healthy"] = True
                continue

            try:
                r = requests.get(url, timeout=5)
                ok = (r.status_code == 200)
                e["__healthy"] = ok
                print(f"[L7][health] {eid} {'OK' if ok else 'DOWN'}")
            except Exception as ex:
                e["__healthy"] = False
                print(f"[L7][health] {eid} EXC: {ex}")

        # 每輪健康檢查後都寫出狀態
        write_status(engines)
        time.sleep(HEALTH_INTERVAL)


def main():
    engines = load_engines()

    # 起一條背景 thread 做健康檢查
    t = threading.Thread(target=health_loop, args=(engines,), daemon=True)
    t.start()

    print("[L7] runner started")

    # 主線程不做事，免得程式退出
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()


os.makedirs(STATUS_DIR, exist_ok=True)

HEALTH_INTERVAL = 15  # 每幾秒做一次健康檢查


def load_engines() -> dict:
    """讀 engines.master.yaml 回來"""
    try:
        with open(MASTER_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print("[L7] load error:", e)
        return {}

    engines = {}
    for item in data.get("engines", []):
        eid = item.get("engine_id")
        if not eid:
            continue
        # 先標記成不健康，待會 health_loop 會更新
        item["__healthy"] = False
        engines[eid] = item
    print(f"[L7] loaded {len(engines)} engines")
    return engines


def write_status(engines: dict):
    """把目前引擎狀態寫到 JSON 檔"""
    data = {"engines": {}}
    for eid, e in engines.items():
        data["engines"][eid] = {
            "name": e.get("engine_name"),
            "enabled": e.get("enabled", False),
            "healthy": e.get("__healthy", False),
        }

    try:
        with open(STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print("[L7] write_status error:", ex)


def health_loop(engines: dict):
    """背景健康檢查"""
    while True:
        for eid, e in engines.items():
            # 沒啟用就直接標不健康
            if not e.get("enabled", False):
                e["__healthy"] = False
                continue

            hc = e.get("healthcheck", {})
            url = hc.get("endpoint")
            if not url:
                # 沒填 health endpoint 就當健康
                e["__healthy"] = True
                continue

            try:
                r = requests.get(url, timeout=5)
                ok = (r.status_code == 200)
                e["__healthy"] = ok
                print(f"[L7][health] {eid} {'OK' if ok else 'DOWN'}")
            except Exception as ex:
                e["__healthy"] = False
                print(f"[L7][health] {eid} EXC: {ex}")

        # 每輪檢查完寫一次檔
        write_status(engines)
        time.sleep(HEALTH_INTERVAL)


def main():
    engines = load_engines()

    t = threading.Thread(target=health_loop, args=(engines,), daemon=True)
    t.start()

    print("[L7] runner started")
    # 主執行緒掛住就好
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
