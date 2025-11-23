#!/usr/bin/env bash

echo "================ Cockswain Health Check ================"
echo "Time:    $(date '+%F %T')"
echo "Host:    $(hostname)"
echo "User:    $(whoami)"
echo "========================================================"
echo

echo "[1] Uptime / Load"
uptime || echo "  (uptime command not available)"
echo

echo "[2] Memory"
free -h || echo "  (free command not available)"
echo

echo "[3] Disk usage (root & /home)"
df -h / /home || echo "  (df command failed)"
echo

echo "[4] Failed systemd units"
systemctl --failed --no-pager || echo "  (systemctl --failed failed)"

echo

echo "[5] Docker containers"
docker ps || echo "  (docker ps failed)"
echo

echo "====================== DONE ============================"
