#!/usr/bin/env python3
import time
import json

def main():
    # 啟動訊息（方便從 journalctl 看啟動時間）
    print("[Arbiter] 判斷核心啟動完成", flush=True)

    # 先用極簡版：只送心跳，不做 stdin 判斷
    while True:
        payload = {
            "timestamp": time.time(),
            "type": "heartbeat",
            "component": "arbiter-core",
            "status": "idle"
        }
        print(json.dumps(payload), flush=True)
        time.sleep(10)

if __name__ == "__main__":
    main()
