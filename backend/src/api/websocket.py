from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from utils.websocket_manager import websocket_manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/tasks/{task_type}")
async def websocket_tasks_endpoint(websocket: WebSocket, task_type: str):
    if task_type not in ["mineru", "audio"]:
        await websocket.close(code=1008)
        return

    try:
        await websocket_manager.connect(websocket, task_type)
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, task_type)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket, task_type)
