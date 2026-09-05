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

    async def emit_log(self, message: str, level: str = "INFO", task_id: str = None, subtask_id: str = None, account_id: str = None):
        """Emit a formatted log event and persist to DB asynchronously if associated with a task"""
        log_data = {
            "message": message,
            "level": level,
            "task_id": task_id,
            "subtask_id": subtask_id,
            "account_id": account_id,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        await self.broadcast("log_append", log_data)
        
        # 若关联了 task_id，异步落盘存储到数据库，确保系统关闭/重启后依然完整可查
        if task_id:
            asyncio.create_task(self._persist_log(message, level, task_id, subtask_id, account_id))

    async def _persist_log(self, message: str, level: str, task_id: str, subtask_id: str = None, account_id: str = None):
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.task import TaskLog
            async with AsyncSessionLocal() as db:
                entry = TaskLog(
                    task_id=task_id,
                    subtask_id=subtask_id,
                    account_id=account_id,
                    level=level,
                    message=message
                )
                db.add(entry)
                await db.commit()
        except Exception:
            pass

    async def emit_screencast(self, frame_b64: str, task_id: str = None, account_id: str = None, title: str = "", url: str = ""):
        """向所有已连接前端广播实时浏览器屏幕推流画面 (CDP Screencast)"""
        await self.broadcast("screencast_frame", {
            "frame": frame_b64,
            "task_id": task_id,
            "account_id": account_id,
            "title": title,
            "url": url,
            "time": datetime.now().strftime("%H:%M:%S")
        })

event_bus = EventBus()
