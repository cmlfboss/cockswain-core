#!/usr/bin/env python3
import sys, json, time, select

def reflect_analysis(event):
    report = {
        "timestamp": time.time(),
        "event": event,
        "consistency": "ok",
        "notes": []
    }

    if event.get("intent") is None:
        report["consistency"] = "warning"
        report["notes"].append("missing intent field")

    if event.get("decision") == "error":
        report["consistency"] = "error"
        report["notes"].append("arbiter decision returned error")

    return report

def main():
    print("[Reflect] 自我反省核心啟動完成", flush=True)

    while True:
        # non-blocking check for stdin input
        r, _, _ = select.select([sys.stdin], [], [], 1)

        if r:
            line = sys.stdin.readline().strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                report = reflect_analysis(data)
                print(json.dumps(report), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)
        else:
            # idle - heartbeat every 10s
            if int(time.time()) % 10 == 0:
                print(json.dumps({
                    "timestamp": time.time(),
                    "type": "heartbeat",
                    "component": "reflect-core"
                }), flush=True)

            time.sleep(1)

if __name__ == "__main__":
    main()
