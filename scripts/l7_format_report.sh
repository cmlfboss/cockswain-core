#!/usr/bin/env bash
# 直接把 l7_monitor_agent 產的資料夾印出來給人看
python3 /srv/cockswain-core/scripts/l7_monitor_agent.py >/dev/null 2>&1
tail -n 200 /srv/cockswain-core/logs/l7-monitor.log
