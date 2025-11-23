#!/usr/bin/env python3
import json, os, time
ALERT_FILE = "/srv/cockswain-core/state/alert.json"
TASK_FILE = "/srv/cockswain-core/state/task_queue.json"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    alert = load_json(ALERT_FILE)
    if not alert:
        print("[trigger-tasks] no alert file found")
        return
    
    queue = []
    if os.path.exists(TASK_FILE):
        queue = load_json(TASK_FILE) or []

    task = None
    if alert.get("status") != "ok":
        task = {
            "id": len(queue) + 1,
            "timestamp": time.strftime("%F %T"),
            "type": "auto_recovery",
            "priority": "high",
            "reason": alert.get("reason"),
            "source": "trigger-tasks"
        }
    else:
        task = {
            "id": len(queue) + 1,
            "timestamp": time.strftime("%F %T"),
            "type": "heartbeat_log",
            "priority": "low",
            "reason": "system normal",
            "source": "trigger-tasks"
        }
    
    queue.append(task)
    save_json(TASK_FILE, queue)
    print(f"[trigger-tasks] appended task {task['id']} ({task['type']})")

if __name__ == "__main__":
    main()
