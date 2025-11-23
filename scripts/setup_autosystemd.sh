#!/usr/bin/env bash
set -e

SCRIPTS_DIR="/srv/cockswain-core/scripts"
PY_SELFCHECK="$SCRIPTS_DIR/task_import_selfcheck.py"
PY_INTENTFILL="$SCRIPTS_DIR/round_engine_intent_fill.py"

echo "🧭 Cockswain auto-detector starting..."

# 0) 先確認兩支 Python 在不在
if [ ! -f "$PY_SELFCHECK" ]; then
  echo "❌ 找不到 $PY_SELFCHECK ，請先確認自檢腳本存在。"
  exit 1
fi

if [ ! -f "$PY_INTENTFILL" ]; then
  echo "❌ 找不到 $PY_INTENTFILL ，請先確認補標腳本存在。"
  exit 1
fi

# 小工具：判斷 service/timer 是否存在
service_exists() {
  systemctl list-unit-files | grep -q "^$1"
}

# ========== 1. 自檢 service ==========
if service_exists "cockswain-selfcheck.service"; then
  echo "✅ cockswain-selfcheck.service 已存在，略過建立"
else
  echo "➕ 建立 cockswain-selfcheck.service"
  sudo tee /etc/systemd/system/cockswain-selfcheck.service >/dev/null <<EOF
[Unit]
Description=Cockswain Core - Daily Selfcheck
After=network.target mysql.service

[Service]
Type=oneshot
WorkingDirectory=$SCRIPTS_DIR
ExecStart=/usr/bin/python3 $PY_SELFCHECK
EOF
fi

# ========== 2. 自檢 timer ==========
if service_exists "cockswain-selfcheck.timer"; then
  echo "✅ cockswain-selfcheck.timer 已存在，略過建立"
else
  echo "➕ 建立 cockswain-selfcheck.timer"
  sudo tee /etc/systemd/system/cockswain-selfcheck.timer >/dev/null <<'EOF'
[Unit]
Description=Cockswain Core - Daily Selfcheck Timer

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
fi

# ========== 3. 補標 service ==========
if service_exists "cockswain-intentfill.service"; then
  echo "✅ cockswain-intentfill.service 已存在，略過建立"
else
  echo "➕ 建立 cockswain-intentfill.service"
  sudo tee /etc/systemd/system/cockswain-intentfill.service >/dev/null <<EOF
[Unit]
Description=Cockswain Core - L2 Intent Fill Engine
After=network.target mysql.service

[Service]
Type=oneshot
WorkingDirectory=$SCRIPTS_DIR
ExecStart=/usr/bin/python3 $PY_INTENTFILL
EOF
fi

# ========== 4. 補標 timer ==========
if service_exists "cockswain-intentfill.timer"; then
  echo "✅ cockswain-intentfill.timer 已存在，略過建立"
else
  echo "➕ 建立 cockswain-intentfill.timer"
  sudo tee /etc/systemd/system/cockswain-intentfill.timer >/dev/null <<'EOF'
[Unit]
Description=Cockswain Core - Intent Fill Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOF
fi


# ========== 5. 每日狀態摘要 service ==========
if service_exists "cockswain-daily-summary.service"; then
  echo "✅ cockswain-daily-summary.service 已存在，略過建立"
else
  echo "➕ 建立 cockswain-daily-summary.service"
  sudo tee /etc/systemd/system/cockswain-daily-summary.service >/dev/null <<EOF
[Unit]
Description=Cockswain Core - Daily Status Summary
After=network.target mysql.service

[Service]
Type=oneshot
WorkingDirectory=$SCRIPTS_DIR
ExecStart=/usr/bin/python3 $SCRIPTS_DIR/daily_status_summary.py
EOF
fi

# ========== 6. 每日狀態摘要 timer ==========
if service_exists "cockswain-daily-summary.timer"; then
  echo "✅ cockswain-daily-summary.timer 已存在，略過建立"
else
  echo "➕ 建立 cockswain-daily-summary.timer"
  sudo tee /etc/systemd/system/cockswain-daily-summary.timer >/dev/null <<'EOF'
[Unit]
Description=Cockswain Core - Daily Status Summary Timer

[Timer]
OnCalendar=*-*-* 07:05:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
fi



# 重新載入 systemd
echo "🔁 重新載入 systemd..."
sudo systemctl daemon-reload

# 啟用 timer（存在就啟用，不存在才會跳掉）
echo "🚀 啟用/啟動 timer..."
sudo systemctl enable --now cockswain-selfcheck.timer 2>/dev/null || true
sudo systemctl enable --now cockswain-intentfill.timer 2>/dev/null || true

echo "✅ 安裝/偵測完成，現在的 cockswain timer："
systemctl list-timers --all | grep cockswain || true
