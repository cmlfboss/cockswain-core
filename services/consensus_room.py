#!/usr/bin/env python3
# /srv/cockswain-core/services/consensus_room.py
# 共識會議聊天室 v0.1

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime

app = FastAPI(title="Cockswain Consensus Room", version="0.1")


class ConnectionManager:
    def __init__(self):
        # room_id -> list[WebSocket]
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict):
        # 把訊息送給這個 room 裡的所有 websocket
        if room_id in self.rooms:
            for ws in self.rooms[room_id]:
                await ws.send_json(message)


manager = ConnectionManager()


@app.get("/")
def root():
    return {"message": "consensus room alive"}


@app.websocket("/ws/{room_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, role: str):
    """
    role 可用：
    - user
    - cockswain_main
    - cockswain_sub
    """
    await manager.connect(room_id, websocket)

    # 廣播加入訊息
    join_msg = {
        "type": "system",
        "time": datetime.utcnow().isoformat(),
        "sender": "system",
        "text": f"{role} joined {room_id}",
    }
    await manager.broadcast(room_id, join_msg)

    try:
        while True:
            text = await websocket.receive_text()
            msg = {
                "type": "message",
                "time": datetime.utcnow().isoformat(),
                "sender": role,
                "text": text,
            }
            await manager.broadcast(room_id, msg)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        leave_msg = {
            "type": "system",
            "time": datetime.utcnow().isoformat(),
            "sender": "system",
            "text": f"{role} left {room_id}",
        }
        await manager.broadcast(room_id, leave_msg)
