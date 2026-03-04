# AudioTaskManager 异步方法 Bug 记录

**日期**: 2026-03-04  
**状态**: 🔄 待修复  
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

### 方案 1: 简化为纯异步实现（推荐）

将 AudioTaskManager 改为纯异步，同时提供异步方法供外部调用：

1. 将所有方法改为 async
2. 修改 `audio_processor.py` 使用 await
3. 修改 `api/audio.py` 使用 await

### 方案 2: 修复同步包装器

使用正确的同步包装模式：
- 使用 `asgiref.sync.async_to_sync`
- 或者使用 `nest_asyncio`（不推荐）

---

## 需要修改的文件

1. `backend/src/audio/task_manager.py`
2. `backend/src/processors/audio_processor.py`
3. `backend/src/api/audio.py`

---

## 相关提交

- `266b629` - 重构: 重写 AudioTaskManager 以使用数据库存储
- `0a83200` - 修复: 将 metadata 字段重命名为 task_metadata
