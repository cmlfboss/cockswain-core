#!/usr/bin/env bash
set -e

echo "🧩 [1/6] 檢查當前 Python SSL 狀態..."
python3 - <<PY
import ssl, sys
print(" - ssl file:", getattr(ssl, "__file__", "<builtin>"))
print(" - has wrap_socket:", hasattr(ssl, "wrap_socket"))
PY

echo "🧩 [2/6] 備份原始 ssl.py（若存在）..."
if [ -f /usr/lib/python3.12/ssl.py ]; then
  sudo cp /usr/lib/python3.12/ssl.py /usr/lib/python3.12/ssl.py.bak_$(date +%Y%m%d_%H%M%S)
  echo "✅ 已備份到 ssl.py.bak_*"
fi

echo "🧩 [3/6] 重新安裝核心 Python 組件與 OpenSSL..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install --reinstall -y   python3.12 python3.12-minimal libpython3.12-stdlib libssl3 python3-venv > /dev/null
echo "✅ 套件重新安裝完成"

echo "🧩 [4/6] 驗證 _ssl 模組是否可載入..."
python3 - <<PY
try:
    import _ssl
    print(" - _ssl:", _ssl.__file__)
except Exception as e:
    print("❌ _ssl 載入失敗:", e)
PY

echo "🧩 [5/6] 再次檢查 ssl.wrap_socket 是否恢復..."
python3 - <<PY
import ssl
print(" - ssl file:", getattr(ssl, "__file__", "<builtin>"))
print(" - has wrap_socket:", hasattr(ssl, "wrap_socket"))
if hasattr(ssl, "wrap_socket"):
    print("✅ wrap_socket 功能恢復正常！")
else:
    print("❌ wrap_socket 仍缺失，請手動檢查。")
PY

echo "🧩 [6/6] 移除暫時補丁 sitecustomize.py（若存在）..."
if [ -f /usr/lib/python3/dist-packages/sitecustomize.py ]; then
  rm /usr/lib/python3/dist-packages/sitecustomize.py
  echo "✅ 已清除暫時補丁"
fi

echo "🏁 修復完成，建議執行："
echo "   sudo systemctl restart cockswain-core-bridge.service"
echo "   tail -n 50 /srv/cockswain-core/logs/core_bridge.log"
