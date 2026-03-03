# WebSocket实时更新功能 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现WebSocket实时更新功能，让前端能够实时接收任务状态变化，无需轮询或手动刷新。

**Problem:**
- 当前前端只能通过手动刷新或轮询获取任务状态更新
- 用户体验不佳，有延迟
- 服务器负载较高（频繁请求）

**Architecture:**
1. 后端添加WebSocket支持（FastAPI原生支持）
2. 创建WebSocketManager管理连接和消息广播
3. 在任务管理器状态更新时触发广播
4. 前端添加WebSocket客户端连接和状态处理

**Tech Stack:** FastAPI + WebSockets + Vue 3

---

## 阶段一：后端WebSocket基础设施

### Task 1: 添加websockets依赖

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: 在dependencies中添加websockets**

```toml
dependencies = [
    "fastapi[uvicorn]>=0.135.1",
    "websockets>=12.0",
    "loguru>=0.7.3",
]
```

**Step 2: Commit**

```bash
cd backend
git add pyproject.toml
git commit -m "feat: 添加websockets依赖"
```

---

### Task 2: 创建WebSocketManager

**Files:**
- Create: `backend/src/utils/websocket_manager.py`

**Step 1: 创建WebSocket管理器**

```python
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
```

**Step 2: Commit**

```bash
cd backend
git add src/utils/websocket_manager.py
git commit -m "feat: 创建WebSocket管理器"
```

---

### Task 3: 添加WebSocket API端点

**Files:**
- Create: `backend/src/api/websocket.py`

**Step 1: 创建WebSocket路由**

```python
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
```

**Step 2: Commit**

```bash
cd backend
git add src/api/websocket.py
git commit -m "feat: 添加WebSocket API端点"
```

---

### Task 4: 在main.py中注册WebSocket路由

**Files:**
- Modify: `backend/main.py`

**Step 1: 导入并注册WebSocket路由**

```python
from api.websocket import router as websocket_router
app.include_router(websocket_router)
```

**Step 2: Commit**

```bash
cd backend
git add main.py
git commit -m "feat: 注册WebSocket路由"
```

---

## 阶段二：集成任务状态广播

### Task 5: 修改MinerU任务管理器集成WebSocket

**Files:**
- Modify: `backend/src/mineru/task_manager.py`

**Step 1: 在update_task中添加广播**

```python
from utils.websocket_manager import websocket_manager

# 在update_task方法中添加
if "state" in kwargs:
    task = await self.get_task(task_id)
    if task:
        await websocket_manager.broadcast_task_update("mineru", {
            "type": "task_update",
            "task_id": task_id,
            "task_type": "mineru",
            "state": kwargs["state"],
            "data": task
        })
```

**Step 2: Commit**

```bash
cd backend
git add src/mineru/task_manager.py
git commit -m "feat: MinerU任务管理器集成WebSocket广播"
```

---

### Task 6: 修改音频任务管理器集成WebSocket

**Files:**
- Modify: `backend/src/audio/task_manager.py`

**Step 1: 在update_task中添加广播**

```python
from utils.websocket_manager import websocket_manager

# 在update_task方法中添加
websocket_manager.broadcast_task_update("audio", {
    "type": "task_update",
    "task_id": task.task_id,
    "task_type": "audio",
    "state": task.status,
    "data": {
        "task_id": task.task_id,
        "status": task.status,
        "file_name": task.file_name
    }
})
```

**Step 2: Commit**

```bash
cd backend
git add src/audio/task_manager.py
git commit -m "feat: 音频任务管理器集成WebSocket广播"
```

---

## 阶段三：前端WebSocket客户端

### Task 7: 创建WebSocket客户端工具

**Files:**
- Create: `app/src/utils/websocket.js`

**Step 1: 创建WebSocket客户端**

```javascript
const DEFAULT_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export class WebSocketClient {
  constructor() {
    this.ws = null
    this.listeners = new Map()
    this.taskType = null
  }

  connect(taskType) {
    this.taskType = taskType
    const url = `${DEFAULT_WS_URL}/ws/tasks/${taskType}`

    this.ws = new WebSocket(url)
    this.ws.onopen = () => this.emit('connected')
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.emit('message', data)
    }
    this.ws.onerror = (error) => this.emit('error', error)
    this.ws.onclose = () => this.emit('disconnected')
  }

  on(event, callback) {
    if (!this.listeners.has(event)) this.listeners.set(event, [])
    this.listeners.get(event).push(callback)
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return
    this.listeners.get(event).forEach(cb => cb(data))
  }

  disconnect() {
    if (this.ws) this.ws.close()
    this.listeners.clear()
  }
}

export const mineruWebSocket = new WebSocketClient()
export const audioWebSocket = new WebSocketClient()
```

**Step 2: Commit**

```bash
cd app
git add src/utils/websocket.js
git commit -m "feat: 创建WebSocket客户端工具"
```

---

### Task 8: 在ParseManagement中集成WebSocket

**Files:**
- Modify: `app/src/views/ParseManagement.vue`

**Step 1: 集成WebSocket**

```javascript
import { mineruWebSocket, audioWebSocket } from '@/utils/websocket'
import { onUnmounted } from 'vue'

function handleWebSocketMessage(message) {
  if (message.type === 'task_update') {
    parseStore.fetchTasks()
    parseStore.fetchStats()
  }
}

onMounted(() => {
  mineruWebSocket.on('message', handleWebSocketMessage)
  audioWebSocket.on('message', handleWebSocketMessage)
  mineruWebSocket.connect('mineru')
  audioWebSocket.connect('audio')
})

onUnmounted(() => {
  mineruWebSocket.off('message', handleWebSocketMessage)
  audioWebSocket.off('message', handleWebSocketMessage)
  mineruWebSocket.disconnect()
  audioWebSocket.disconnect()
})
```

**Step 2: Commit**

```bash
cd app
git add src/views/ParseManagement.vue
git commit -m "feat: ParseManagement集成WebSocket实时更新"
```

---

## 执行总结

### 完成标准
- [ ] Task 1-4: 后端WebSocket基础设施完成
- [ ] Task 5-6: 任务状态广播集成完成
- [ ] Task 7-8: 前端WebSocket客户端完成

---

**Plan complete and saved to `.opencode/plans/2026-03-03-websocket-realtime-updates.md`.**
