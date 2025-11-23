#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 /srv/cockswain-core/logs/observer/health.log 轉成 JSON 陣列
輸出：/tmp/health-index.json
每行格式預期：
2025-11-08 23:10:00 cpu_temp=62°C disk_usage=18% warn=0
"""

import json
import os
from datetime import datetime

LOG_PATH = "/srv/cockswain-core/logs/observer/health.log"
OUT_PATH = "/tmp/health-index.json"

records = []

if not os.path.exists(LOG_PATH):
    print(f"[log-indexer] log file not found: {LOG_PATH}")
    with open(OUT_PATH, "w") as f:
        json.dump([], f)
    exit(0)

with open(LOG_PATH, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 3:
            # 格式怪怪的就跳過
            continue

        timestamp = f"{parts[0]} {parts[1]}"

        # 後面的全部都是 key=value
        data = {}
        for kv in parts[2:]:
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            data[k] = v

        # 標準欄位
        data["timestamp"] = timestamp
        # 給 Meili 當主鍵用
        # 例：health-2025-11-08T23:10:00
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            data["id"] = "health-" + dt.isoformat()
        except Exception:
            # 不行就用原字串
            data["id"] = "health-" + timestamp.replace(" ", "T")

        records.append(data)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"[log-indexer] exported {len(records)} records → {OUT_PATH}")
