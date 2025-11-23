#!/usr/bin/env python3
import json
import os
from datetime import datetime

SRC = "/srv/cockswain-core/state/system_state.json"
OUT = "/srv/cockswain-core/state/system_state_latest.json"

latest = None

if os.path.exists(SRC):
    with open(SRC, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
else:
    data = []

for item in data:
    # 如果有 timestamp 就用 timestamp 比較，沒有就用 id
    ts_str = item.get("timestamp")
    if ts_str:
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            ts = None
    else:
        ts = None

    if latest is None:
        latest = (ts, item)
    else:
        old_ts, _ = latest
        # 兩種情況：新時間比較新；或者舊的沒有時間，就用新的
        if (ts and old_ts and ts > old_ts) or (ts and not old_ts):
            latest = (ts, item)
        else:
            # 沒時間就用 id 最大
            if not ts and item.get("id", 0) > latest[1].get("id", 0):
                latest = (ts, item)

# 寫出結果
os.makedirs("/srv/cockswain-core/state", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(latest[1] if latest else {}, f, ensure_ascii=False, indent=2)

print(f"[get-latest-system-state] wrote {OUT}")
