#!/usr/bin/env bash
set -e

# 1) 基本變數
BASE_DIR="/srv/cockswain-core"
SCRIPT_DIR="$BASE_DIR/scripts"
LOG_DIR="$BASE_DIR/logs/tests"
SERVICE_NAME="cockswain-test-api"
PORT="7800"
USER_NAME="cocksmain"

echo "[*] 建立必要目錄..."
sudo mkdir -p "$SCRIPT_DIR"
sudo mkdir -p "$LOG_DIR"
sudo chown -R $USER_NAME:$USER_NAME "$BASE_DIR"

echo "[*] 安裝必要套件 (fastapi + uvicorn)..."
sudo apt update
sudo apt install -y python3-fastapi uvicorn

echo "[*] 產生 FastAPI 測試端點：$SCRIPT_DIR/test_endpoint.py"
cat << 'EOF' | sudo tee $SCRIPT_DIR/test_endpoint.py > /dev/null
from fastapi import FastAPI, Request
import json, os, datetime

app = FastAPI()
LOG_PATH = "/srv/cockswain-core/logs/tests"
os.makedirs(LOG_PATH, exist_ok=True)

@app.post("/api/store")
async def store_data(req: Request):
    data = await req.json()
    filename = f"test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(LOG_PATH, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "saved_to": filepath}

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.datetime.now().isoformat()}
EOF

sudo chown $USER_NAME:$USER_NAME $SCRIPT_DIR/test_endpoint.py

echo "[*] 建立 systemd 服務：/etc/systemd/system/$SERVICE_NAME.service"
cat << EOF | sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null
[Unit]
Description=Cockswain Test API (FastAPI on $PORT)
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/uvicorn test_endpoint:app --host 127.0.0.1 --port $PORT
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

echo "[*] 重新載入 systemd 並啟動服務..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "[*] 建立簡單的自我回報腳本：$SCRIPT_DIR/self_report.sh"
cat << 'EOF' | sudo tee $SCRIPT_DIR/self_report.sh > /dev/null
#!/usr/bin/env bash
TS=$(date --iso-8601=seconds)
curl -s -X POST http://127.0.0.1:7800/api/store \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"mother-cron\",
    \"timestamp\": \"${TS}\",
    \"user\": \"system\",
    \"topic\": \"mother-health-report\",
    \"payload\": {
      \"message\": \"Mother node heartbeat from cron at ${TS}\"
    }
  }" > /dev/null
EOF
sudo chmod +x $SCRIPT_DIR/self_report.sh
sudo chown $USER_NAME:$USER_NAME $SCRIPT_DIR/self_report.sh

echo "[*] 若要加入排程，可執行："
echo "    (crontab -l 2>/dev/null; echo \"*/15 * * * * $SCRIPT_DIR/self_report.sh\") | crontab -"
echo "[*] 安裝完成！"
echo "[*] 測試：curl http://127.0.0.1:7800/health"
echo "[*] 或送一筆：curl -X POST http://127.0.0.1:7800/api/store -H 'Content-Type: application/json' -d '{\"source\":\"test\",\"payload\":{\"msg\":\"hello cockswain\"}}'"
