# WebSocket实时更新功能实施报告

**日期**: 2026-03-03  
**状态**: ✅ 已完成

## 概述

实现 WebSocket 实时更新功能，让前端能够实时接收任务状态变化，无需轮询或手动刷新。

## 问题

- 当前前端只能通过手动刷新或轮询获取任务状态更新
- 用户体验不佳，有延迟
- 服务器负载较高（频繁请求）

## 技术架构

**技术栈**: FastAPI + WebSockets + Vue 3

### 系统架构

```
┌─────────────────┐         WebSocket         ┌─────────────────┐
│   前端 (Vue)    │ ◄───────────────────────► │  后端 (FastAPI) │
│                 │   /ws/tasks/{task_type}   │                 │
│ - WebSocketClient│                           │ - WebSocketManager│
│ - 事件监听      │                           │ - 连接管理      │
│ - 状态更新      │                           │ - 消息广播      │
└─────────────────┘                           └────────┬────────┘
                                                      │
                                                      │ 触发
                                                      │
                                         ┌────────────┴────────────┐
                                         │                         │
                                ┌────────▼────────┐      ┌────────▼────────┐
                                │ MinerU 任务管理 │      │  音频任务管理   │
                                │   task_manager  │      │   task_manager  │
                                └─────────────────┘      └─────────────────┘
```

## 实现内容

### 阶段一：后端WebSocket基础设施

#### Task 1: 添加 websockets 依赖

**文件**: `backend/pyproject.toml`

```toml
dependencies = [
    "fastapi[uvicorn]>=0.135.1",
    "websockets>=12.0",
    "loguru>=0.7.3",
    ...
]
```

#### Task 2: 创建 WebSocketManager

**文件**: `backend/src/utils/websocket_manager.py`

**核心功能**:
- 按任务类型管理连接集合（mineru、audio）
- 连接/断开处理
- 任务状态更新广播
- 异常处理和自动清理失效连接

```python
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

    async def broadcast_task_update(self, task_type: str, message: dict):
        # 广播任务更新到所有连接的客户端
        ...
```

#### Task 3: 添加 WebSocket API 端点

**文件**: `backend/src/api/websocket.py`

**端点**:
- `GET /ws/tasks/{task_type}` - WebSocket 连接端点

**功能**:
- 验证任务类型（mineru/audio）
- 管理连接生命周期
- 处理断开连接

#### Task 4: 注册 WebSocket 路由

**文件**: `backend/main.py`

```python
from api.websocket import router as websocket_router
app.include_router(websocket_router)
```

### 阶段二：集成任务状态广播

#### Task 5: MinerU 任务管理器集成

**文件**: `backend/src/mineru/task_manager.py`

**变更**:
- 导入 `websocket_manager`
- 在 `update_task` 方法中添加状态变更广播
- 广播消息包含任务类型、状态、完整数据

```python
if "state" in kwargs:
    if task:
        await websocket_manager.broadcast_task_update("mineru", {
            "type": "task_update",
            "task_id": task_id,
            "task_type": "mineru",
            "state": kwargs["state"],
            "data": self._task_to_dict(task)
        })
```

#### Task 6: 音频任务管理器集成

**文件**: `backend/src/audio/task_manager.py`

**变更**:
- 导入 `websocket_manager` 和 `asyncio`
- 在 `update_task` 方法中添加状态变更广播
- 使用 `asyncio.create_task()` 异步发送广播

```python
asyncio.create_task(websocket_manager.broadcast_task_update("audio", {
    "type": "task_update",
    "task_id": task.task_id,
    "task_type": "audio",
    "state": task.status,
    "data": {
        "task_id": task.task_id,
        "status": task.status,
        "file_name": task.file_name
    }
}))
```

### 阶段三：前端WebSocket客户端

#### Task 7: 创建 WebSocket 客户端工具

**文件**: `app/src/utils/websocket.js`

**核心类**: `WebSocketClient`

**功能**:
- WebSocket 连接管理
- 事件监听系统（on/off/emit）
- 自动重连机制（预留）
- 消息解析和分发

**预配置实例**:
- `mineruWebSocket` - MinerU 任务连接
- `audioWebSocket` - 音频任务连接

```javascript
export class WebSocketClient {
  connect(taskType) { ... }
  on(event, callback) { ... }
  off(event, callback) { ... }
  emit(event, data) { ... }
  disconnect() { ... }
}

export const mineruWebSocket = new WebSocketClient()
export const audioWebSocket = new WebSocketClient()
```

#### Task 8: ParseManagement 集成

**文件**: `app/src/views/ParseManagement.vue`

**变更**:
- 导入 WebSocket 客户端
- 在 `onMounted` 中建立连接并监听消息
- 在 `onUnmounted` 中清理连接
- 收到 `task_update` 消息时自动刷新任务列表和统计

```javascript
function handleWebSocketMessage(message) {
  if (message.type === 'task_update') {
    parseStore.fetchTasks()
    parseStore.fetchStats()
  }
}

onMounted(async () => {
  // ... 原有初始化代码

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

## 消息格式

### 任务更新消息

```json
{
  "type": "task_update",
  "task_id": "uuid",
  "task_type": "mineru|audio",
  "state": "pending|running|done|failed",
  "data": {
    // 完整任务数据
  }
}
```

## 变更文件清单

**新增文件**:
- `backend/src/utils/websocket_manager.py` - WebSocket 管理器
- `backend/src/api/websocket.py` - WebSocket API 端点
- `app/src/utils/websocket.js` - WebSocket 客户端工具

**修改文件**:
- `backend/pyproject.toml` - 添加 websockets 依赖
- `backend/main.py` - 注册 WebSocket 路由
- `backend/src/mineru/task_manager.py` - 集成 WebSocket 广播
- `backend/src/audio/task_manager.py` - 集成 WebSocket 广播
- `app/src/views/ParseManagement.vue` - 集成 WebSocket 实时更新

## 测试建议

### 功能测试

1. **连接测试**
   - 打开解析管理页面
   - 检查浏览器开发者工具 Network 标签
   - 确认 WebSocket 连接已建立（状态 101 Switching Protocols）

2. **MinerU 任务状态更新**
   - 添加 PDF 文件到解析队列
   - 开始解析
   - 观察任务状态是否自动从 pending → running → done/failed
   - 无需手动刷新页面

3. **音频任务状态更新**
   - 添加音频文件到解析队列
   - 开始转录
   - 观察任务状态是否自动更新
   - 统计数据是否实时刷新

4. **多标签页测试**
   - 在多个浏览器标签页打开解析管理
   - 在一个标签页启动任务
   - 观察其他标签页是否同步更新

### 性能测试

1. **连接稳定性**
   - 长时间保持页面打开
   - 确认 WebSocket 连接不会意外断开

2. **消息延迟**
   - 测量任务状态变更到前端更新的延迟
   - 预期延迟 < 100ms

3. **并发连接**
   - 模拟多个客户端同时连接
   - 确认后端能稳定处理

## 用户体验改进

- ✅ **实时更新**: 任务状态变更立即反映，无需手动刷新
- ✅ **降低延迟**: 从轮询延迟（几秒）降到实时（毫秒级）
- ✅ **减轻服务器负载**: 减少无效的 HTTP 请求
- ✅ **多标签同步**: 多个标签页自动保持同步

## 后续优化建议

1. **自动重连机制**
   - WebSocket 断开时自动尝试重连
   - 指数退避策略

2. **连接状态指示**
   - 在 UI 上显示 WebSocket 连接状态
   - 离线时提示用户

3. **消息队列**
   - 离线时缓存消息
   - 重连后同步状态

4. **权限验证**
   - 添加 WebSocket 连接时的权限验证
   - 防止未授权访问

5. **更多事件类型**
   - 支持进度更新消息
   - 支持日志流式输出

## 相关文档

- [实施计划](../plans/2026-03-03-websocket-realtime-updates.md)
- [解析管理功能文档](../features/parse-management.md)
