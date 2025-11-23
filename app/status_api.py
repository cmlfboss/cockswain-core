#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import json

STATE_DIR = "/srv/cockswain-core/state"
ALERT_FILE = os.path.join(STATE_DIR, "alert.json")
LATEST_FILE = os.path.join(STATE_DIR, "system_state_latest.json")
TASK_FILE = os.path.join(STATE_DIR, "task_queue.json")

app = FastAPI(title="Cockswain Status API")

@app.get("/ping")
def ping():
    return {"ok": True, "service": "cockswain-status-api"}

@app.get("/status")
def get_status():
    if not os.path.exists(ALERT_FILE):
        raise HTTPException(status_code=404, detail="alert.json not found")
    with open(ALERT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)

@app.get("/latest")
def get_latest():
    if not os.path.exists(LATEST_FILE):
        raise HTTPException(status_code=404, detail="system_state_latest.json not found")
    with open(LATEST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)

@app.get("/tasks")
def get_tasks():
    # 回傳目前任務佇列
    if not os.path.exists(TASK_FILE):
        # 沒有就給空陣列
        return JSONResponse(content=[])
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        try:
            tasks = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="task_queue.json is corrupted")
    return JSONResponse(content=tasks)
