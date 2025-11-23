#!/usr/bin/env bash
set -e

BASE="/srv/cockswain-core"
LOG_DIR="$BASE/logs"
mkdir -p "$LOG_DIR"
OUT="$LOG_DIR/status_collect.log"

ts() { date '+%F %T'; }

echo "[$(ts)] === mother status collect ===" >> "$OUT"

# 1) docker 總體
if command -v docker >/dev/null 2>&1; then
  echo "[$(ts)] docker ps:" >> "$OUT"
  sudo docker ps --format '  {{.Names}} {{.Status}} {{.Ports}}' >> "$OUT" 2>&1 || true
else
  echo "[$(ts)] docker not found" >> "$OUT"
fi

# 2) mysql 健康度
if sudo docker ps --format '{{.Names}}' | grep -q '^cockswain-mysql$'; then
  ROOTPW=$(sudo awk -F= '/MYSQL_ROOT_PASSWORD/ {print $2}' /srv/cockswain-core/.env 2>/dev/null || true)
  if [ -n "$ROOTPW" ]; then
    sudo docker exec cockswain-mysql mysql -u root -p"$ROOTPW" -e "SELECT 'mysql ok';" >/dev/null 2>&1 \
      && echo "[$(ts)] mysql: healthy" >> "$OUT" \
      || echo "[$(ts)] mysql: UNHEALTHY" >> "$OUT"
  else
    echo "[$(ts)] mysql: NO PASSWORD FOUND" >> "$OUT"
  fi
else
  echo "[$(ts)] mysql: container not found" >> "$OUT"
fi

# 3) meilisearch 健康度（你的版本回的是 "available"）
MEILI_HEALTH=$(curl -s http://127.0.0.1:7700/health || true)
if echo "$MEILI_HEALTH" | grep -q '"status":"available"'; then
  echo "[$(ts)] meilisearch: healthy" >> "$OUT"
else
  echo "[$(ts)] meilisearch: not responding (resp='$MEILI_HEALTH')" >> "$OUT"
fi

# 4) 本地 AI endpoint
AI_HEALTH=$(curl -s http://127.0.0.1:8000/ || true)
if echo "$AI_HEALTH" | grep -q '"status":"ok"'; then
  echo "[$(ts)] ai-core: healthy" >> "$OUT"
else
  echo "[$(ts)] ai-core: not responding (resp='$AI_HEALTH')" >> "$OUT"
fi

echo "[$(ts)] === status end ===" >> "$OUT"
