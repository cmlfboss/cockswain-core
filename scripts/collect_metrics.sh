#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"
LOG_DIR="$BASE_DIR/logs"
LOG="$LOG_DIR/collect_metrics.log"
mkdir -p "$LOG_DIR"

# 讀 .env
if [ -f "$ENV_FILE" ]; then
  set -a
  grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' > /tmp/cockswain-env.$$
  . /tmp/cockswain-env.$$
  rm /tmp/cockswain-env.$$
  set +a
fi

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_ROOT_USER="${MYSQL_ROOT_USER:-root}"
: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD missing in .env}"
: "${MYSQL_DATABASE:?MYSQL_DATABASE missing in .env}"

# 取本機 IP
NODE_IP=$(ip -4 addr show | awk '/inet / && $2 !~ /127\.0\.0\.1/ && $2 !~ /169\.254\./ {split($2,a,"/"); print a[1]; exit}')

# CPU (簡單取一次 /proc/stat)
read cpu user nice system idle iowait irq softirq steal guest guest_nice < /proc/stat
total=$((user+nice+system+idle+iowait+irq+softirq+steal))
idle_old=$idle
total_old=$total
sleep 0.5
read cpu user nice system idle iowait irq softirq steal guest guest_nice < /proc/stat
total=$((user+nice+system+idle+iowait+irq+softirq+steal))
idle_new=$idle
total_new=$total
diff_total=$((total_new - total_old))
diff_idle=$((idle_new - idle_old))
if [ "$diff_total" -gt 0 ]; then
  cpu_usage=$(echo "scale=2; (1 - $diff_idle / $diff_total) * 100" | bc -l)
else
  cpu_usage=0
fi

# MEM
mem_usage=$(free -m | awk '/Mem:/ {printf "%.2f", $3*100/$2}')

# LOAD
read load1 load5 load15 rest < /proc/loadavg

# DISK /
disk_root=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')

# UPTIME
read up_secs _ < /proc/uptime
up_secs=${up_secs%.*}

# 寫入 DB
SQL="USE \`$MYSQL_DATABASE\`;
INSERT INTO metrics
  (node_ip, cpu_percent, mem_percent, load_1m, load_5m, load_15m, disk_root_percent, uptime_seconds)
VALUES
  ('$NODE_IP', $cpu_usage, $mem_usage, $load1, $load5, $load15, $disk_root, $up_secs);"

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
  -e "$SQL" \
  && echo "$(date '+%F %T') metrics collected for $NODE_IP" >> "$LOG"
