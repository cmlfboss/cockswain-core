#!/bin/bash
# Cockswain Core MySQL Helper v1.0
# Role : 讀取 .env 的 DB_*，一鍵登入 cockswain DB
# Owner: L7 / 舵手

set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "[mysql-core] 找不到 $ENV_FILE"
  exit 1
fi

# 只抓需要的變數（不做 export，避免外洩）
DB_HOST=$(grep -E '^DB_HOST=' "$ENV_FILE" | cut -d'=' -f2-)
DB_NAME=$(grep -E '^DB_NAME=' "$ENV_FILE" | cut -d'=' -f2-)
DB_USER=$(grep -E '^DB_USER=' "$ENV_FILE" | cut -d'=' -f2-)
DB_PASSWORD=$(grep -E '^DB_PASSWORD=' "$ENV_FILE" | cut -d'=' -f2-)

if [ -z "$DB_HOST" ]; then
  DB_HOST="localhost"
fi

if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
  echo "[mysql-core] DB_NAME 或 DB_USER 空白，請檢查 $ENV_FILE"
  exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
  echo "[mysql-core] DB_PASSWORD 為空，請檢查 $ENV_FILE"
  exit 1
fi

echo "[mysql-core] 使用 .env 中的設定登入："
echo "  - host = $DB_HOST"
echo "  - db   = $DB_NAME"
echo "  - user = $DB_USER"
echo "（密碼由 .env 載入，無需手動輸入）"

# exec 取代當前 process，避免在 shell history 中留額外資訊
exec mysql \
  -h "$DB_HOST" \
  -u "$DB_USER" \
  "-p$DB_PASSWORD" \
  "$DB_NAME"
