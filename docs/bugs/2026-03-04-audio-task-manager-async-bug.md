# AudioTaskManager 异步方法 Bug 记录

**日期**: 2026-03-04  
**状态**: ✅ 已修复  
**严重程度**: 高

---

## 问题描述

AudioTaskManager 的异步方法实现存在问题，导致音频转录任务无法正常工作。

## 错误日志

### 错误 1: add_task 未被 await
```
E:\Code\workSpace\GitBank\QBase\backend\src\processors\audio_processor.py:72: RuntimeWarning: coroutine 'AudioTaskManager.add_task' was never awaited
  self.task_manager.add_task(task)
```

### 错误 2: 事件循环冲突
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

发生在 `get_task()`、`update_task()`、`get_all_tasks()` 等同步包装方法中。

---

## 问题根因

### 问题 1: add_task 变为异步方法
- 重写后的 `AudioTaskManager.add_task()` 是异步方法
- 但 `audio_processor.py` 中调用时没有使用 `await`

### 问题 2: 同步包装器逻辑错误
当前的同步包装器实现：
```python
def get_task(self, task_id: str) -> Optional[AudioTaskInfo]:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = asyncio.create_task(self._get_task_async(task_id))
            return loop.run_until_complete(task)  # ❌ 错误：不能在运行的循环中调用
        else:
            return loop.run_until_complete(self._get_task_async(task_id))
    except RuntimeError:
        return asyncio.run(self._get_task_async(task_id))  # ❌ 错误：不能在已有循环中调用
```

---

## 修复方案

采用**纯异步实现**方案：

1. 将 AudioTaskManager 所有方法改为 async
2. 修改 `audio_processor.py` 使用 await
3. 修改 `api/audio.py` 使用 await

---

## 修复详情

### 任务 1: 重写 AudioTaskManager 为纯异步

**文件**: `backend/src/audio/task_manager.py`

**修改内容**:
- 移除所有同步包装方法（`get_task`, `update_task`, `get_all_tasks`, `remove_task`）
- 重命名异步方法：`_get_task_async` → `get_task`，以此类推
- 保持 `add_task` 为异步方法
- 修复 `_remove_task_async` 中的错误（使用 `session` 而不是 `self.db`）

**提交**: `0ceaf58`

---

### 任务 2: 修改 AudioProcessor 使用 await

**文件**: `backend/src/processors/audio_processor.py`

**修改内容**:
- 第 72 行：`self.task_manager.add_task(task)` → `await self.task_manager.add_task(task)`
- 第 77 行：`self.task_manager.get_task(task_id)` → `await self.task_manager.get_task(task_id)`
- 第 85 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
- 第 105 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
- 第 120 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
- 第 140 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
- 第 147 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
- 第 155 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
- 第 166 行：`self.task_manager.get_task(task_id)` → `await self.task_manager.get_task(task_id)`
- 第 171 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`

**提交**: `f2b0989`

---

### 任务 3: 修改音频 API 使用 await

**文件**: `backend/src/api/audio.py`

**修改内容**:
- 第 114 行：`audio_task_manager.get_task(task_id)` → `await audio_task_manager.get_task(task_id)`
- 第 123 行：`audio_task_manager.get_task(task_id)` → `await audio_task_manager.get_task(task_id)`
- 第 144 行：`audio_task_manager.get_all_tasks()` → `await audio_task_manager.get_all_tasks()`
- 第 151 行：`audio_task_manager.get_task(task_id)` → `await audio_task_manager.get_task(task_id)`
- 第 155 行：`audio_task_manager.remove_task(task_id)` → `await audio_task_manager.remove_task(task_id)`

**提交**: `aefbe6e`

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/audio/task_manager.py` | 重写为纯异步 |
| `backend/src/processors/audio_processor.py` | 添加 await 调用 |
| `backend/src/api/audio.py` | 添加 await 调用 |

---

## 相关提交

- `266b629` - 重构: 重写 AudioTaskManager 以使用数据库存储
- `0a83200` - 修复: 将 metadata 字段重命名为 task_metadata
- `0ceaf58` - 修复: 重写 AudioTaskManager 为纯异步实现
- `f2b0989` - 修复: 修改 AudioProcessor 使用 await 调用异步方法
- `aefbe6e` - 修复: 修改音频 API 使用 await 调用异步方法

---

## 验证清单

- [x] AudioTaskManager 所有方法改为 async
- [x] AudioProcessor 所有调用添加 await
- [x] 音频 API 所有调用添加 await
- [ ] 后端启动无错误
- [ ] 音频上传任务创建成功
- [ ] 音频转录任务正常处理
- [ ] 任务状态可查询
- [ ] 任务结果可获取
- [ ] 任务列表可获取
- [ ] 任务可删除
- [ ] 数据正确存储到数据库
- [ ] WebSocket 实时更新正常
