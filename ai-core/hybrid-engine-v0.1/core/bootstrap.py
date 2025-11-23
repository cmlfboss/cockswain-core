#!/usr/bin/env python3
import time, json

def main():
    print("[HybridEngine] Bootstrap 啟動")
    while True:
        status = {
            "timestamp": time.time(),
            "status": "running",
            "component": "hybrid-engine",
            "message": "舵手核心啟動中"
        }
        print(json.dumps(status))
        time.sleep(10)

if __name__ == "__main__":
    main()
