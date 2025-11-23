#!/usr/bin/env bash
set -e

LOG_DIR="/srv/cockswain-core/logs"
mkdir -p "$LOG_DIR"

REPORT="$LOG_DIR/env_report.log"
echo "=== Cockswain Mother Env Report ===" > "$REPORT"
date >> "$REPORT"

echo "[*] Checking Docker..." | tee -a "$REPORT"
if systemctl is-active --quiet docker; then
  echo "OK: docker is running" | tee -a "$REPORT"
else
  echo "ERR: docker is NOT running" | tee -a "$REPORT"
fi

echo "[*] Checking UFW..." | tee -a "$REPORT"
if command -v ufw >/dev/null 2>&1; then
  ufw status verbose >> "$REPORT" 2>&1 || true
else
  echo "WARN: ufw not installed" | tee -a "$REPORT"
fi

echo "[*] Checking fail2ban..." | tee -a "$REPORT"
if systemctl is-active --quiet fail2ban; then
  sudo fail2ban-client status >> "$REPORT" 2>&1 || true
else
  echo "WARN: fail2ban not running" | tee -a "$REPORT"
fi

echo "[*] Checking directories..." | tee -a "$REPORT"
for d in /srv/cockswain-core /srv/cockswain-home; do
  if [ -d "$d" ]; then
    echo "OK: $d exists" | tee -a "$REPORT"
  else
    echo "WARN: $d missing" | tee -a "$REPORT"
  fi
done

echo "Env check done. Report: $REPORT"
