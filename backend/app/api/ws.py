from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.event_bus import event_bus

router = APIRouter(tags=["WebSocket 实时通信"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    统一 WebSocket 双向长连接端点
    前端连接后可实时接收日志流、二维码 Base64 刷新及账号/任务状态流变通知
    """
    await event_bus.connect(websocket)
    try:
        while True:
            # 接收前端的心跳或指令
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await event_bus.disconnect(websocket)
    except Exception:
        await event_bus.disconnect(websocket)
