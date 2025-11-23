#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
l7_monitor_agent.py
第七層：收集第六層的成果 + 系統服務狀態，必要時通知
"""
import os
import sys
import json
import datetime
from pathlib import Path

import yaml
import subprocess


BASE_DIR = Path("/srv/cockswain-core")
CFG_FILE = BASE_DIR / "config" / "l7_config.yaml"
LOG_FILE = BASE_DIR / "logs" / "l7-monitor.log"


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")


def load_config():
    if not CFG_FILE.exists():
        raise SystemExit(f"config not found: {CFG_FILE}")
    with CFG_FILE.open() as f:
        return yaml.safe_load(f)


def load_tasks(done_dir: Path, limit: int = 30):
    if not done_dir.exists():
        return []
    tasks = []
    for p in sorted(done_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_file"] = str(p)
            tasks.append(data)
            if len(tasks) >= limit:
                break
        except Exception as e:
            log(f"read task {p} failed: {e}")
    return tasks


def load_services(services_json: Path):
    if not services_json.exists():
        return []
    try:
        data = json.loads(services_json.read_text(encoding="utf-8"))
        return data.get("services", [])
    except Exception as e:
        log(f"read services.json failed: {e}")
        return []


def tail_log(log_path: Path, max_lines: int = 100):
    if not log_path.exists():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        return lines[-max_lines:]
    except Exception:
        return []


def build_report(cfg: dict):
    paths = cfg.get("paths", {})
    done_dir = Path(paths.get("tasks_done", "/srv/cockswain-core/tasks/done"))
    services_json = Path(paths.get("services_json", "/srv/cockswain-core/tmp/services.json"))
    l6_log = Path(paths.get("l6_log", "/srv/cockswain-core/logs/l6-dispatch.log"))

    report_cfg = cfg.get("report", {})
    max_tasks = int(report_cfg.get("max_recent_tasks", 30))
    max_log_lines = int(report_cfg.get("max_recent_log_lines", 100))

    tasks = load_tasks(done_dir, limit=max_tasks)
    services = load_services(services_json)
    l6_lines = tail_log(l6_log, max_log_lines)

    # 統計任務結果
    stats = {"DONE": 0, "FAILED": 0, "RETRYING": 0, "OTHER": 0}
    for t in tasks:
        st = t.get("status", "OTHER")
        if st in stats:
            stats[st] += 1
        else:
            stats["OTHER"] += 1

    # 找出不健康服務
    bad_services = []
    for s in services:
        # active=running 視為正常，其它視為需要注意
        if s.get("active") not in ("running", "exited"):
            bad_services.append(s)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"[L7 REPORT] {now}")
    lines.append("")
    lines.append("== Task Summary ==")
    lines.append(f"DONE: {stats['DONE']} | FAILED: {stats['FAILED']} | RETRYING: {stats['RETRYING']} | OTHER: {stats['OTHER']}")
    lines.append("")
    lines.append("== Recent Tasks ==")
    for t in tasks:
        lines.append(f"- {t.get('task_type')} {t.get('service_name','')} [{t.get('status')}] src={t.get('source','')} file={t.get('_file','')}")
    lines.append("")
    lines.append("== Services ==")
    if services:
      for s in services:
        mark = "OK"
        if s.get("active") not in ("running", "exited"):
            mark = "BAD"
        lines.append(f"- {s.get('name')} [{s.get('active')}] {mark}")
    else:
      lines.append("(no services.json)")
    lines.append("")
    lines.append("== L6 tail ==")
    for l in l6_lines:
        lines.append(l)

    return "\n".join(lines), stats, bad_services


def send_alert(cfg: dict, report_text: str):
    alerts = cfg.get("alerts", {})
    if not alerts.get("enabled", False):
        log("alerts disabled, skip")
        return
    cmd = alerts.get("cmd")
    if not cmd or not Path(cmd).exists():
        log(f"alert cmd {cmd} not found, skip")
        return
    # 把 report 塞進去
    try:
        proc = subprocess.run(cmd, input=report_text, text=True, shell=True)
        log(f"alert sent via {cmd} rc={proc.returncode}")
    except Exception as e:
        log(f"alert error: {e}")


def main():
    cfg = load_config()
    report_text, stats, bad_services = build_report(cfg)
    log("L7 report generated")

    need_alert = False
    if cfg.get("report", {}).get("alert_on_failed_tasks", True) and stats.get("FAILED", 0) > 0:
        need_alert = True
    if cfg.get("report", {}).get("alert_on_service_failed", True) and bad_services:
        need_alert = True

    if need_alert:
        send_alert(cfg, report_text)
    else:
        # 至少留下報表在 log 裡
        log("no alert triggered")
        LOG_FILE.write_text(LOG_FILE.read_text() + report_text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
