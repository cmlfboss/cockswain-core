#!/usr/bin/env python3
# /srv/cockswain-core/services/sync_gateway.py
# 雙舵手資料同步閘道 v0.1

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import mysql.connector
import json
import os

app = FastAPI(title="Cockswain Sync Gateway", version="0.1")

DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_USER = os.getenv("MYSQL_USER", "cockswain_core")
DB_PASS = os.getenv("MYSQL_PASSWORD", "CHANGE_ME")
DB_NAME = os.getenv("MYSQL_DATABASE", "cockswain")

class AgentDelta(BaseModel):
    agent_id: str
    version: str | None = None
    payload: dict
    note: str | None = None

def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

@app.post("/api/agents/sync")
def sync_agent(delta: AgentDelta):
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_deltas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                agent_id VARCHAR(64),
                version VARCHAR(64),
                payload JSON,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        insert_sql = """
            INSERT INTO agent_deltas (agent_id, version, payload, note)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(
            insert_sql,
            (
                delta.agent_id,
                delta.version or datetime.utcnow().isoformat(),
                json.dumps(delta.payload, ensure_ascii=False),
                delta.note
            )
        )
        db.commit()
        return {"ok": True, "message": "delta stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
            db.close()
        except:
            pass

@app.get("/api/agents/latest/{agent_id}")
def get_latest(agent_id: str):
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM agent_deltas
            WHERE agent_id=%s
            ORDER BY created_at DESC
            LIMIT 1
        """, (agent_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="no delta")
        return row
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
            db.close()
        except:
            pass
