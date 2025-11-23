#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import os
import subprocess
import uuid
from datetime import datetime

PORT = 7801

# 這個是 /srv/cockswain-core/ai-core
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

TASK_DIR = os.path.join(BASE_DIR, "tempstore", "tasks")
os.makedirs(TASK_DIR, exist_ok=True)


def get_hybrid_status():
    """讀取 Hybrid-Core 最新狀態（心跳）"""
    try:
        result = subprocess.check_output(
            ["journalctl", "-u", "cockswain-hybrid.service", "-n", "1", "--no-pager"]
        ).decode("utf-8")
        return {"hybrid_status": result.strip()}
    except Exception as e:
        return {"hybrid_status": f"error: {e}"}


class L7Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, data, status: int = 200):
        """統一輸出 JSON 的小工具"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """處理 GET 請求，目前提供 / 與 /status"""
        if self.path == "/" or self.path.startswith("/status"):
            payload = {
                "l7_status": "running",
                "timestamp": time.time(),
                "hybrid": get_hybrid_status(),
            }
            self._send_json(payload, status=200)
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        """處理 POST 請求，目前提供 /task（自動化編輯入口＋寫入任務檔）"""
        if self.path.startswith("/task"):
            # 讀取請求 body
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length > 0 else b"{}"

            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                payload = {}

            task_type = payload.get("task_type", "unknown")
            content = payload.get("content", "")

            # 建立 task_id，寫入 tempstore/tasks
            task_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            task_obj = {
                "task_id": task_id,
                "created_at": now,
                "task_type": task_type,
                "content": content,
                "source": "l7-api",
                "status": "queued",
            }

            task_path = os.path.join(TASK_DIR, f"{task_id}.json")
            try:
                with open(task_path, "w", encoding="utf-8") as f:
                    json.dump(task_obj, f, ensure_ascii=False, indent=2)
                stored_ok = True
                error_msg = ""
            except Exception as e:
                stored_ok = False
                error_msg = str(e)

            resp = {
                "timestamp": time.time(),
                "endpoint": "/task",
                "received": True,
                "task_type": task_type,
                "task_id": task_id,
                "storage": {
                    "path": task_path,
                    "saved": stored_ok,
                    "error": error_msg,
                },
                "content_preview": content[:80] + ("..." if len(content) > 80 else ""),
                "status": "queued" if stored_ok else "error",
                "note": "L7 已接收並嘗試寫入任務檔，後續可由 arbiter / reflect / editor 處理。",
            }

            self._send_json(resp, status=200 if stored_ok else 500)
        else:
            self._send_json({"error": "Not found"}, status=404)


def run():
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, L7Handler)
    print(f"[L7] Orchestrator listening on {PORT} ...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
