#!/usr/bin/env python3
import os, json, time, traceback
from pathlib import Path

BASE = Path("/srv/cockswain-core")
TASK_INBOX = BASE / "tasks" / "inbox"
TASK_PROCESSED = BASE / "tasks" / "processed"
LOG_FILE = BASE / "logs" / "ai-core.log"

AGENTS_DIR = BASE / "agents"
AGENT_FILES = [
    AGENTS_DIR / "helmsman_alpha.yml",
    AGENTS_DIR / "helmsman_beta.yml",
]

from pipelines.l1_intent import process as l1
from pipelines.l2_common import process as l2
from pipelines.l3_knowledge import process as l3
from pipelines.l4_domain import process as l4
from pipelines.l5_judgement import process as l5
from pipelines.l6_correction import process as l6
from pipelines.l7_cognition import process as l7

def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def load_task(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_task(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_pipeline(payload: dict, agent_conf: dict):
    ctx = {"agent": agent_conf}
    data = payload
    data = l1(data, ctx)
    data = l2(data, ctx)
    data = l3(data, ctx)
    data = l4(data, ctx)
    data = l5(data, ctx)
    data = l6(data, ctx)
    data = l7(data, ctx)
    return data

def load_agent_conf(path: Path):
    conf = {"name": path.stem}
    if not path.exists():
        return conf
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                conf[k.strip()] = v.strip()
    return conf

def main():
    log("🧠 cockswain ai-bridge started (hybrid test mode)")
    TASK_INBOX.mkdir(parents=True, exist_ok=True)
    TASK_PROCESSED.mkdir(parents=True, exist_ok=True)

    agents = [load_agent_conf(p) for p in AGENT_FILES]

    while True:
        for task_file in TASK_INBOX.glob("*.json"):
            try:
                task = load_task(task_file)
                for agent in agents:
                    enriched = run_pipeline(task, agent)
                    out_path = TASK_PROCESSED / f"{task_file.stem}_{agent['name']}.json"
                    save_task(out_path, enriched)
                    log(f"✅ processed {task_file.name} as {agent['name']}")
                task_file.unlink()
            except Exception as e:
                log(f"❌ error processing {task_file.name}: {e}")
                log(traceback.format_exc())
        time.sleep(2)

if __name__ == "__main__":
    main()
