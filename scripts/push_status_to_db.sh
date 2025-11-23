#!/usr/bin/env bash
set -e

BASE="/srv/cockswain-core"
LOG_DIR="$BASE/logs"
mkdir -p "$LOG_DIR"
OUT="$LOG_DIR/push_status_to_db.log"

ts() { date '+%F %T'; }

# 讀密碼
ROOTPW=$(sudo awk -F= '/MYSQL_ROOT_PASSWORD/ {print $2}' /srv/cockswain-core/.env 2>/dev/null || true)
if [ -z "$ROOTPW" ]; then
  echo "[$(ts)] no MYSQL_ROOT_PASSWORD found" >> "$OUT"
  exit 0
fi

# docker 列表（做成一行文字）
DOCKER_PS=$(sudo docker ps --format '{{.Names}} {{.Status}} {{.Ports}}' 2>/dev/null | sed ':a;N;$!ba;s/\n/; /g')

# mysql 狀態
MYSQL_STATUS="unknown"
if sudo docker ps --format '{{.Names}}' | grep -q '^cockswain-mysql$'; then
  if sudo docker exec cockswain-mysql mysql -u root -p"$ROOTPW" -e "SELECT 1;" >/dev/null 2>&1; then
    MYSQL_STATUS="healthy"
  else
    MYSQL_STATUS="unhealthy"
  fi
else
  MYSQL_STATUS="notfound"
fi

# meili 狀態
MEILI_STATUS="unknown"
MEILI_HEALTH=$(curl -s http://127.0.0.1:7700/health || true)
if echo "$MEILI_HEALTH" | grep -q '"status":"available"'; then
  MEILI_STATUS="healthy"
else
  MEILI_STATUS="unhealthy"
fi

# ai 狀態
AI_STATUS="unknown"
AI_HEALTH=$(curl -s http://127.0.0.1:8000/ || true)
if echo "$AI_HEALTH" | grep -q '"status":"ok"'; then
  AI_STATUS="healthy"
else
  AI_STATUS="unhealthy"
fi

# 寫進資料庫
sudo docker exec -i cockswain-mysql \
  mysql -u root -p"$ROOTPW" cockswain <<SQL >> "$OUT" 2>&1
INSERT INTO mother_status_log (docker_json, mysql_status, meili_status, ai_status)
VALUES ('${DOCKER_PS//\'/\'\'}', '$MYSQL_STATUS', '$MEILI_STATUS', '$AI_STATUS');
SQL

echo "[$(ts)] push done" >> "$OUT"
