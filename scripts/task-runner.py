#!/usr/bin/env python3
import json, os, subprocess, time

TASK_FILE = "/srv/cockswain-core/state/task_queue.json"
LOG_FILE = "/srv/cockswain-core/logs/observer/task-runner.log"

# 任務型別對應要跑的指令
ACTION_MAP = {
    "heartbeat_log": None,  # 不需要跑外部指令
    "auto_recovery": "/srv/cockswain-core/scripts/push-health-to-mysql.sh",
    "cleanup_repo": "/srv/cockswain-core/scripts/move_inbound_to_repo.sh",
}

def load_tasks():
    if not os.path.exists(TASK_FILE):
        return []
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_tasks(tasks):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def append_log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%F %T')} {msg}\n")

def run_command(cmd):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120
        )
        return (result.returncode == 0, result.stdout)
    except Exception as e:
        return (False, str(e))

def main():
    tasks = load_tasks()
    changed = False

    for task in tasks:
        status = task.get("status")
        if status in (None, "pending"):
            ttype = task.get("type")
            cmd = ACTION_MAP.get(ttype)

            if cmd is None:
                # 不用外部指令的任務
                task["status"] = "done"
                task["result"] = "no action required"
                append_log(f"[task-runner] task {task.get('id')} ({ttype}) marked done (no action)")
            else:
                ok, output = run_command(cmd)

                # 清掉 MySQL 一直碎念的那個警告
                if output:
                    output = output.replace(
                        "mysql: [Warning] Using a password on the command line interface can be insecure.\n",
                        ""
                    )

                task["status"] = "done" if ok else "failed"
                task["result"] = output[-500:] if output else ""
                append_log(f"[task-runner] task {task.get('id')} ({ttype}) run {'OK' if ok else 'FAIL'}")

            task["done_at"] = time.strftime("%F %T")
            changed = True

    if changed:
        # 超過 200 筆就只留最新的 200 筆，避免檔案長到爆
        if len(tasks) > 200:
            tasks = tasks[-200:]
        save_tasks(tasks)

    print("[task-runner] done")

if __name__ == "__main__":
    main()
