#!/bin/bash
set -euo pipefail

BASE_DIR="/srv/cockswain-core"
ENV_FILE="$BASE_DIR/.env"

DB_NAME="cockswain"
DB_USER="cockswain_core"
DB_PASS="PFFDoFAyxWDnTPWEhl7X+pSzLHcg3bM1"

timestamp="$(date +%Y%m%d_%H%M%S)"

echo "[db-bootstrap] BASE_DIR = $BASE_DIR"
echo "[db-bootstrap] ENV_FILE = $ENV_FILE"
echo "[db-bootstrap] DB_NAME  = $DB_NAME"
echo "[db-bootstrap] DB_USER  = $DB_USER"

# 1) .env 備份 + 準備
if [ -f "$ENV_FILE" ]; then
  echo "[db-bootstrap] 發現既有 .env，先做備份：$ENV_FILE.bak.$timestamp"
  cp "$ENV_FILE" "$ENV_FILE.bak.$timestamp"
else
  echo "[db-bootstrap] 沒有 .env，建立新檔案"
  touch "$ENV_FILE"
fi

upsert_env() {
  local var="$1"
  local val="$2"

  if grep -qE "^${var}=" "$ENV_FILE"; then
    # 用 sed 更新既有行
    sed -i "s/^${var}=.*/${var}=${val}/" "$ENV_FILE"
  else
    # 追加新行
    printf '%s=%s\n' "$var" "$val" >> "$ENV_FILE"
  fi
}

echo "[db-bootstrap] 更新 .env 內的 DB 相關設定"
upsert_env "DB_HOST" "localhost"
upsert_env "DB_NAME" "$DB_NAME"
upsert_env "DB_USER" "$DB_USER"
upsert_env "DB_PASSWORD" "$DB_PASS"

# 2) MySQL 端建立 DB / 帳號 / 權限
echo "[db-bootstrap] 連線 MySQL，建立資料庫與帳號..."

sudo mysql <<EOF2
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
ALTER USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';

CREATE USER IF NOT EXISTS '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
ALTER USER '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';

GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'127.0.0.1';

FLUSH PRIVILEGES;
EOF2

echo "[db-bootstrap] MySQL 帳號與權限設定完成"

# 3) 簡單連線測試（用剛寫入的密碼做動態驗證）
echo "[db-bootstrap] 進行連線測試（使用 env / DB_PASS）..."

MYSQL_PWD="$DB_PASS" mysql -u "$DB_USER" -h "127.0.0.1" "$DB_NAME" -e "SELECT 'OK' AS db_status, CURRENT_USER() AS user\G" >/tmp/db_bootstrap_check.log 2>&1 || {
  echo "[db-bootstrap] 連線測試失敗，詳情見 /tmp/db_bootstrap_check.log"
  exit 1
}

echo "[db-bootstrap] 連線測試通過 ✔"
echo "[db-bootstrap] .env 已完成更新："
echo "  - DB_HOST=localhost"
echo "  - DB_NAME=$DB_NAME"
echo "  - DB_USER=$DB_USER"
echo "  - DB_PASSWORD=***（已寫入 .env，無需人工記憶）"
echo
echo "[db-bootstrap] 可以刪除本腳本或限制權限："
echo "  chmod 700 $BASE_DIR/scripts/db_bootstrap_cockswain_core.sh"
