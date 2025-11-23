#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
l6_task_dispatcher.py v1.2
- 支援任務優先權
- 支援失敗重試
- system-repair 少參數就直接 FAIL，不要一直重試
"""
import json
import subprocess
import datetime
from pathlib import Path
import yaml

BASE_DIR = Path("/srv/cockswain-core")
LOG_FILE = BASE_DIR / "logs" / "l6-dispatch.log"
SCHEMA_FILE = BASE_DIR / "config" / "l6_behavior_schema.yaml"


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")


def load_schema():
    with SCHEMA_FILE.open() as f:
        return yaml.safe_load(f)


def load_tasks(pending_dir: Path):
    pending_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for task_file in pending_dir.glob("*.json"):
      try:
        data = json.loads(task_file.read_text(encoding="utf-8"))
        data["_file"] = task_file
        tasks.append(data)
      except Exception as e:
        log(f"ERROR: read {task_file} failed: {e}")
    return tasks


def match_action(schema, task_type: str):
    for rule in schema.get("dispatch_rules", []):
        if rule.get("match", {}).get("task_type") == task_type:
            return rule
    return None


def render_cmd(cmd_template: str, task_data: dict):
    cmd = cmd_template
    for k, v in task_data.items():
        if isinstance(v, str):
            cmd = cmd.replace(f"{{{{{k}}}}}", v)
    cmd = cmd.replace("{{service_name}}", "").strip()
    return " ".join(cmd.split())


def run_cmd(cmd: str):
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return res.returncode, res.stdout, res.stderr


def save_task(task_file: Path, data: dict):
    data = dict(data)
    data.pop("_file", None)
    task_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    schema = load_schema()
    defaults = schema.get("defaults", {})
    max_retries = int(defaults.get("max_retries", 3))
    pending_dir = Path(defaults.get("pending_dir"))
    done_dir = Path(defaults.get("done_dir"))
    done_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(pending_dir)

    def task_priority(t):
        rule = match_action(schema, t.get("task_type", "generic"))
        if rule and "priority" in rule:
            return -int(rule["priority"])
        return 0

    tasks.sort(key=task_priority)
    actions = schema.get("actions", {})

    for task in tasks:
        task_file: Path = task["_file"]
        task_type = task.get("task_type", "generic")
        retries = int(task.get("retries", 0))

        rule = match_action(schema, task_type)
        if not rule:
            log(f"WARNING: no rule for task_type={task_type}, keep in pending")
            continue

        action_name = rule.get("action")
        action = actions.get(action_name)
        if not action:
            log(f"WARNING: action {action_name} not defined")
            continue

        # 🛡️ 防呆：system-repair 必須要有 service_name
        if task_type == "system-repair" and not task.get("service_name"):
            log(f"ERROR: system-repair task {task_file.name} missing service_name, mark FAILED")
            task["status"] = "FAILED"
            save_task(task_file, task)
            target = done_dir / task_file.name
            task_file.rename(target)
            log(f"MOVE {task_file.name} -> {target}")
            continue

        cmd_template = action.get("cmd", "")
        cmd = render_cmd(cmd_template, task)

        log(f"dispatch task {task_file.name} type={task_type} action={action_name} retries={retries} cmd='{cmd}'")
        rc, out, err = run_cmd(cmd)
        log(f"EXEC rc={rc}")
        if out:
            log(f"STDOUT: {out.strip()}")
        if err:
            log(f"STDERR: {err.strip()}")

        if rc == 0:
            task["status"] = "DONE"
            save_task(task_file, task)
            target = done_dir / task_file.name
            task_file.rename(target)
            log(f"MOVE {task_file.name} -> {target}")
        else:
            retries += 1
            task["retries"] = retries
            if retries >= max_retries:
                task["status"] = "FAILED"
                save_task(task_file, task)
                target = done_dir / task_file.name
                task_file.rename(target)
                log(f"MAX RETRIES reached. MOVE {task_file.name} -> {target}")
            else:
                task["status"] = "RETRYING"
                save_task(task_file, task)
                log(f"RETRY scheduled ({retries}/{max_retries}) for {task_file.name}")

    log("l6 dispatch cycle done.")
