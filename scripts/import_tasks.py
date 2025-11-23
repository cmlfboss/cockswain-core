#!/usr/bin/env python3
import json
from pathlib import Path
import datetime

BASE = Path("/srv/cockswain-core")
PROCESSED = BASE / "tasks" / "processed"
ARCHIVE = BASE / "tasks" / "archived"
LOG = BASE / "logs" / "import-tasks.log"

# 確保路徑存在
ARCHIVE.mkdir(parents=True, exist_ok=True)
LOG.parent.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def import_one(path: Path):
    # 之後這裡可以換成真正的 DB insert
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    log(f"imported: {path.name} at {datetime.datetime.now().isoformat()}")
    target = ARCHIVE / path.name
    path.rename(target)

def main():
    files = list(PROCESSED.glob("*.json"))
    if not files:
        log("no processed tasks.")
        return
    for f in files:
        import_one(f)

if __name__ == "__main__":
    main()
