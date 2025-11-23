#!/usr/bin/env python3
import sys, json, os

if len(sys.argv) != 3:
    print("usage: export-system-state.py <input-tsv> <output-json>")
    sys.exit(1)

tsv_path = sys.argv[1]
json_path = sys.argv[2]

rows = []
if os.path.exists(tsv_path):
    with open(tsv_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            row = {
                "id": int(parts[0]),
                "timestamp": parts[1],
                "cpu_temp": parts[2],
                "disk_usage": parts[3],
                "warn": int(parts[4]),
                "source": parts[5],
                "note": parts[6],
            }
            rows.append(row)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
