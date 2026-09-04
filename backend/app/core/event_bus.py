import asyncio
import json
from typing import Set, Any, Dict
from fastapi import WebSocket
from datetime import datetime

class EventBus:
    """Async in-memory pub-sub event bus and WebSocket manager"""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, event: str, data: Dict[str, Any]):
        """Broadcast an event payload to all connected WebSockets"""
        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        text = json.dumps(payload, ensure_ascii=False)
        
        async with self._lock:
            disconnected = []
            for ws in self.active_connections:
                try:
                    await ws.send_text(text)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                self.active_connections.remove(ws)

    async def emit_log(self, message: str, level: str = "INFO", task_id: str = None, account_id: str = None):
        """Emit a formatted log event"""
        await self.broadcast("log_append", {
            "message": message,
            "level": level,
            "task_id": task_id,
            "account_id": account_id,
            "time": datetime.now().strftime("%H:%M:%S")
        })

event_bus = EventBus()
