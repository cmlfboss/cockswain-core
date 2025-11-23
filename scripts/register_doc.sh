#!/usr/bin/env bash
set -euo pipefail

# 用法檢查
if [ $# -lt 1 ]; then
  echo "usage: $0 /path/to/doc.ext"
  exit 1
fi

FILEPATH="$1"
BASENAME=$(basename "$FILEPATH")
DIRNAME=$(dirname "$FILEPATH")

LOG="/srv/cockswain-core/logs/register_doc.log"
mkdir -p "$(dirname "$LOG")"

# 1) 檢查檔案存在
if [ ! -f "$FILEPATH" ]; then
  echo "$(date '+%F %T') ERROR: file not found: $FILEPATH" | tee -a "$LOG"
  exit 1
fi

# 2) 抓本機 IP：先試 192.168.*，沒有再用原本的第一個
SELF_IP=$(ip -4 addr show | awk '/inet / && $2 ~ /^192\.168\./ {split($2,a,"/"); print a[1]; exit}')
if [ -z "$SELF_IP" ]; then
  SELF_IP=$(hostname -I | awk '{print $1}')
fi

# 3) DB 設定（沿用你現在的）
MYSQL_HOST="127.0.0.1"
MYSQL_PORT="3306"
MYSQL_DATABASE="cockswain"
MYSQL_ROOT_USER="debian-sys-maint"
MYSQL_ROOT_PASSWORD="yQpp9N9Y7klY4ILU"

# 4) 寫入資料庫
mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u "$MYSQL_ROOT_USER" -p"$MYSQL_ROOT_PASSWORD" \
  -D "$MYSQL_DATABASE" \
  -e "INSERT INTO doc_registry (filename, path, node_ip)
      VALUES ('$BASENAME', '$DIRNAME', '$SELF_IP')
      ON DUPLICATE KEY UPDATE node_ip='$SELF_IP', created_at=NOW();"

echo "$(date '+%F %T') registered $FILEPATH (ip=$SELF_IP)" | tee -a "$LOG"
