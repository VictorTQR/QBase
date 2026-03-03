from typing import Dict, Set
from fastapi import WebSocket
from loguru import logger


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "mineru": set(),
            "audio": set(),
        }
        self.task_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_type: str):
        await websocket.accept()
        if task_type in self.active_connections:
            self.active_connections[task_type].add(websocket)

    async def connect_to_task(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(websocket)

    def disconnect(self, websocket: WebSocket, task_type: str):
        if task_type in self.active_connections:
            self.active_connections[task_type].discard(websocket)

    def disconnect_from_task(self, websocket: WebSocket, task_id: str):
        if task_id in self.task_connections:
            self.task_connections[task_id].discard(websocket)
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]

    async def broadcast_task_update(self, task_type: str, message: dict):
        if task_type not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[task_type]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.add(connection)

        for connection in disconnected:
            self.active_connections[task_type].discard(connection)


websocket_manager = WebSocketManager()
