#!/usr/bin/env python3
import json
import os

LATEST = "/srv/cockswain-core/state/system_state_latest.json"
OUT = "/srv/cockswain-core/state/alert.json"

status = {
    "status": "unknown",
    "reason": "",
    "source": "evaluate-system-state",
}

# 讀最新一筆
if os.path.exists(LATEST):
    with open(LATEST, "r", encoding="utf-8") as f:
        try:
            latest = json.load(f)
        except json.JSONDecodeError:
            latest = {}
else:
    latest = {}

if not latest:
    status["status"] = "no-data"
    status["reason"] = "no latest system_state found"
else:
    # 預設 ok
    status["status"] = "ok"
    status["reason"] = "all metrics under threshold"
    status["timestamp"] = latest.get("timestamp")

    # 1) warn 欄位
    warn = int(latest.get("warn", 0))

    # 2) 溫度（可能是字串 '62'）
    cpu_raw = latest.get("cpu_temp", "")
    try:
        cpu_val = int(str(cpu_raw).replace("°C", "").strip())
    except ValueError:
        cpu_val = None

    # 3) 磁碟
    disk_raw = latest.get("disk_usage", "")
    try:
        disk_val = int(str(disk_raw).replace("%", "").strip())
    except ValueError:
        disk_val = None

    # 規則判斷
    reasons = []

    if warn == 1:
        status["status"] = "alert"
        reasons.append("warn flag = 1")

    if cpu_val is not None and cpu_val > 85:
        status["status"] = "alert"
        reasons.append(f"cpu_temp {cpu_val}°C > 85°C")

    if disk_val is not None and disk_val > 90:
        status["status"] = "alert"
        reasons.append(f"disk_usage {disk_val}% > 90%")

    if reasons:
        status["reason"] = "; ".join(reasons)

# 寫出 alert.json
os.makedirs("/srv/cockswain-core/state", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(status, f, ensure_ascii=False, indent=2)

print(f"[evaluate-system-state] wrote {OUT}")
