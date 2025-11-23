#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
orchestrator.py
Cockswain Task Orchestrator (with local LLM via Ollama)

流程：
1. HTTP POST /execute 進來，內容大概是：
   {
     "task_id": 3,
     "agent": "default",
     "payload": {...任務內容...}
   }

2. 我們做簡單的模型選擇：
   - 有 SQL 味道 → db-assistant
   - 有 code/程式/python → code-assistant
   - 其他 → local-llm

3. 如果是 local-llm，就去打本機的 Ollama：
   http://127.0.0.1:11434/api/generate
   model 用 "phi3"（你可以改）

4. 不管成功失敗，都寫一筆到 task_runs，方便 L5 做自省

5. 回一個 JSON 給 core_bridge，讓它把 tasks_inbox 更新成 done/failed
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
import urllib.request

# ====== MySQL 設定（跟你現在系統一致）======
MYSQL_DB = "cockswain"
MYSQL_USER = "cockswain_core"
MYSQL_PASSWORD = "cSWN!_2025-m0ther-N0de#1"
MYSQL_SOCKET = "/var/run/mysqld/mysqld.sock"

# ====== HTTP 設定 ======
ORCH_PORT = int(os.environ.get("ORCH_PORT", "9002"))

# ====== Ollama 設定 ======
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "phi3"  # 你如果 pull 了別的就改這裡


def get_db():
    """取得 DB 連線（走 UNIX socket，避免 SSL 那個舊問題）"""
    return mysql.connector.connect(
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        unix_socket=MYSQL_SOCKET,
        ssl_disabled=True,
    )


def ensure_task_runs_table():
    """第一次啟動時確保有 task_runs 這張表"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS task_runs (
          id INT AUTO_INCREMENT PRIMARY KEY,
          task_id INT,
          agent VARCHAR(64),
          backend VARCHAR(64),
          status VARCHAR(32),
          result_text TEXT,
          started_at DATETIME,
          ended_at DATETIME,
          cost_token INT NULL,
          cost_ms INT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def model_selector(payload: dict) -> str:
    """
    很簡單的路由，先有就好：
    - 有 select/from → db-assistant
    - 有 code/程式/python → code-assistant
    - 其他 → local-llm
    """
    txt = json.dumps(payload, ensure_ascii=False).lower()
    if "select " in txt and " from " in txt:
        return "db-assistant"
    if "code" in txt or "程式" in txt or "python" in txt:
        return "code-assistant"
    return "local-llm"


def run_backend(backend: str, payload: dict) -> dict:
    """
    真正執行的地方
    - local-llm → 打 Ollama
    - 其他先回假資料
    """
    if backend == "local-llm":
        # 組 prompt
        prompt = (
            payload.get("msg")
            or payload.get("prompt")
            or json.dumps(payload, ensure_ascii=False)
        )
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": True,
                "backend": backend,
                "msg": res.get("response", ""),
                "raw": res,
            }
        except Exception as e:
            return {
                "ok": False,
                "backend": backend,
                "error": str(e),
            }

    # 其他 backend 先假裝成功，之後你要接別的就從這裡長出去
    return {
        "ok": True,
        "backend": backend,
        "echo": payload,
        "msg": f"simulated execution by {backend}",
    }


def record_run(
    task_id: int, agent: str, backend: str, status: str, result_text: str
) -> None:
    """把這次執行記錄到 L5 表裡"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO task_runs (task_id, agent, backend, status, result_text, started_at, ended_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """,
        (task_id, agent, backend, status, result_text[:1000]),
    )
    conn.commit()
    cur.close()
    conn.close()


class OrchestratorHandler(BaseHTTPRequestHandler):
    def _json(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self):
        if self.path != "/execute":
            self._json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            self._json(400, {"error": "invalid json"})
            return

        # core_bridge 會這樣送進來：
        # {
        #   "task_id": 3,
        #   "agent": "default",
        #   "payload": {...}
        # }
        task_id = req.get("task_id")
        agent = req.get("agent", "default")
        payload = req.get("payload", {})

        backend = model_selector(payload)
        result = run_backend(backend, payload)

        # 寫執行紀錄
        if task_id is not None:
            record_run(
                task_id,
                agent,
                backend,
                "done" if result.get("ok") else "failed",
                json.dumps(result, ensure_ascii=False),
            )

        # 回給 core_bridge
        if result.get("ok"):
            self._json(
                200,
                {
                    "ok": True,
                    "backend": backend,
                    "detail": f"task executed by {backend}",
                },
            )
        else:
            self._json(
                200,
                {
                    "ok": False,
                    "backend": backend,
                    "detail": result.get("error", "backend failed"),
                },
            )


def run():
    ensure_task_runs_table()
    server = HTTPServer(("0.0.0.0", ORCH_PORT), OrchestratorHandler)
    print(f"[orchestrator] running on 0.0.0.0:{ORCH_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
