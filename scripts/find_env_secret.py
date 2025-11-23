#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import hashlib
import datetime
import re

BASE = Path("/srv/cockswain-core")
LOG = BASE / "logs" / "secret-scan.log"

TARGET_EXT = {
    ".env", ".env.example", ".env.local",
    ".sh", ".bash", ".yml", ".yaml",
    ".txt", ".ini", ".py",
}

KEY_PATTERNS = [
    "MYSQL_PASSWORD",
    "MYSQL_USER",
    "MYSQL_HOST",
    "MYSQL_DATABASE",
    "DB_PASSWORD",
    "DB_USER",
    "DB_HOST",
    "DB_NAME",
    "API_KEY",
    "SECRET_KEY",
    "TOKEN",
    "ACCESS_KEY",
    "PRIVATE_KEY",
]

ENV_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*$")

def log(msg: str):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"[{ts}] {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

def short_hash(value: str) -> str:
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return h[:10]

def line_suspect(line: str) -> bool:
    for k in KEY_PATTERNS:
        if k in line:
            return True
    if ENV_LINE_RE.match(line):
        return True
    return False

def mask_value(val: str) -> str:
    val = val.strip().strip('"').strip("'")
    if not val:
        return "<EMPTY>"
    return f"<MASKED len={len(val)} hash={short_hash(val)}>"

def scan_file(path: Path):
    rel = path.relative_to(BASE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, raw in enumerate(f, start=1):
                line = raw.rstrip("\n")
                if not line_suspect(line):
                    continue
                m = ENV_LINE_RE.match(line)
                if m:
                    key = m.group(1)
                    val = m.group(2)
                    masked = mask_value(val)
                    log(f"FOUND {rel}:{idx} KEY={key} VALUE={masked}")
                else:
                    masked = mask_value(line)
                    log(f"FOUND {rel}:{idx} RAW={masked}")
    except (UnicodeDecodeError, PermissionError) as e:
        log(f"SKIP {rel} ({e})")

def main():
    log("=== secret scan start ===")
    if not BASE.exists():
        log("BASE not exists, abort.")
        return
    for path in BASE.rglob("*"):
        if path.is_file():
            if path.suffix in TARGET_EXT or path.name in (".env", "docker-compose.yml", "docker-compose.yaml"):
                scan_file(path)
    log("=== secret scan done ===")

if __name__ == "__main__":
    main()
