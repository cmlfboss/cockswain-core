#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consensus_arbiter.py
Cockswain L7 Consensus Arbiter (scoring version)
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

import mysql.connector

# ====== DB 設定 ======
MYSQL_DB = "cockswain"
MYSQL_USER = "cockswain_core"
# 這個就是你前面在 MySQL 裡設的那組，Python 可以放驚嘆號沒問題
MYSQL_PASSWORD = "cSWN!_2025-m0ther-N0de#1"
MYSQL_SOCKET = "/var/run/mysqld/mysqld.sock"

ARB_PORT = int(os.environ.get("ARB_PORT", "9001"))

# 核准最低分數
MIN_SCORE = 40


def get_db():
    return mysql.connector.connect(
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        unix_socket=MYSQL_SOCKET,
        ssl_disabled=True,
    )


def get_agent_stat(agent_name: str):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM agent_stats WHERE agent=%s", (agent_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_backend_stat(backend: str):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM backend_stats WHERE backend=%s", (backend,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def agent_has_service(agent_name: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM eco_services WHERE agent_name=%s AND status='active'",
        (agent_name,),
    )
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return count > 0


def decide_default_agent(payload: dict) -> str:
    txt = json.dumps(payload, ensure_ascii=False).lower()
    if "python" in txt or "code" in txt or "程式" in txt:
        return "code-assistant"
    if "sql" in txt or "select " in txt:
        return "db-assistant"
    return "default"


def score_candidate(agent_name: str, backend_hint: str | None = None) -> dict:
    score = 0
    reasons: list[str] = []

    # 有註冊服務就加分
    if agent_has_service(agent_name):
        score += 20
        reasons.append("service registered in eco_services")
    else:
        reasons.append("no active service in eco_services")

    # 看 agent 成績
    a_stat = get_agent_stat(agent_name)
    if a_stat:
        total = a_stat.get("total_runs") or 0
        success = a_stat.get("success_runs") or 0
        if total > 0:
            succ_rate = int(success * 100 / total)
            if succ_rate >= 95:
                score += 40
            elif succ_rate >= 80:
                score += 30
            elif succ_rate >= 50:
                score += 15
            else:
                score += 5
            reasons.append(f"agent success rate {succ_rate}%")
        else:
            score += 5
            reasons.append("agent has no history")
    else:
        reasons.append("no agent_stats record")

    # 看 backend
    if backend_hint:
        b_stat = get_backend_stat(backend_hint)
        if b_stat:
            b_total = b_stat.get("total_runs") or 0
            b_success = b_stat.get("success_runs") or 0
            if b_total > 0:
                b_rate = int(b_success * 100 / b_total)
                if b_rate >= 95:
                    score += 20
                elif b_rate >= 80:
                    score += 15
                elif b_rate >= 50:
                    score += 8
                else:
                    score += 2
                reasons.append(f"backend {backend_hint} success {b_rate}%")
            else:
                score += 5
                reasons.append(f"backend {backend_hint} no history")
        else:
            reasons.append(f"backend {backend_hint} no stats")

    return {
        "agent": agent_name,
        "score": score,
        "reasons": reasons,
    }


class ArbiterHandler(BaseHTTPRequestHandler):
    def _json(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        if self.path != "/decide":
            self._json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            self._json(400, {"error": "invalid json"})
            return

        task_id = req.get("task_id")
        payload = req.get("payload") or {}
        preferred_agent = req.get("preferred_agent")
        backend_hint = req.get("backend")

        if preferred_agent:
            candidate = preferred_agent
        else:
            candidate = decide_default_agent(payload)

        scored = score_candidate(candidate, backend_hint)
        approved = scored["score"] >= MIN_SCORE

        resp = {
            "ok": True,
            "approved": approved,
            "task_id": task_id,
            "chosen_agent": scored["agent"] if approved else None,
            "score": scored["score"],
            "reasons": scored["reasons"],
            "ts": datetime.utcnow().isoformat() + "Z",
        }
        self._json(200, resp)


def run():
    server = HTTPServer(("0.0.0.0", ARB_PORT), ArbiterHandler)
    print(f"[arbiter] running on 0.0.0.0:{ARB_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
