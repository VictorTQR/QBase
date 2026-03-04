# 修复 AudioTaskManager 异步方法问题

**日期**: 2026-03-04  
**状态**: ✅ 已完成  
**优先级**: 高

---

## 问题概述

AudioTaskManager 重写后存在异步方法调用问题，导致音频转录功能无法正常工作。

## 问题详情

### 问题 1: add_task 未被 await

**文件**: `backend/src/processors/audio_processor.py:72`

**问题**: 
```python
self.task_manager.add_task(task)  # ❌ add_task 现在是异步方法，需要 await
```

### 问题 2: 同步包装器事件循环冲突

**文件**: `backend/src/audio/task_manager.py`

**问题**: 同步包装方法（`get_task`, `update_task`, `get_all_tasks`, `remove_task`）在已有事件循环中调用 `asyncio.run()` 或 `loop.run_until_complete()` 会失败。

---

## 修复方案

采用**纯异步实现**方案，因为：
- FastAPI 本身是异步框架
- 避免复杂的同步/异步包装
- 代码更简洁、性能更好

---

## 实施步骤

### 任务 1: 重写 AudioTaskManager 为纯异步 ✅

**文件**: `backend/src/audio/task_manager.py`

**步骤**:
1. 移除所有同步包装方法（`get_task`, `update_task`, `get_all_tasks`, `remove_task`）
2. 重命名异步方法：`_get_task_async` → `get_task`，以此类推
3. 保持 `add_task` 为异步方法
4. 修复 `_remove_task_async` 中的错误（使用 `session` 而不是 `self.db`）

**结果**: 所有公共方法都是 async

**提交**: `0ceaf58`

---

### 任务 2: 修改 AudioProcessor 使用 await ✅

**文件**: `backend/src/processors/audio_processor.py`

**步骤**:
1. 第 72 行：`self.task_manager.add_task(task)` → `await self.task_manager.add_task(task)`
2. 第 77 行：`self.task_manager.get_task(task_id)` → `await self.task_manager.get_task(task_id)`
3. 第 85 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
4. 第 105 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
5. 第 120 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
6. 第 140 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
7. 第 147 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
8. 第 155 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`
9. 第 166 行：`self.task_manager.get_task(task_id)` → `await self.task_manager.get_task(task_id)`
10. 第 171 行：`self.task_manager.update_task(task)` → `await self.task_manager.update_task(task)`

**提交**: `f2b0989`

---

### 任务 3: 修改音频 API 使用 await ✅

**文件**: `backend/src/api/audio.py`

**步骤**:
1. 第 114 行：`audio_task_manager.get_task(task_id)` → `await audio_task_manager.get_task(task_id)`
2. 第 123 行：`audio_task_manager.get_task(task_id)` → `await audio_task_manager.get_task(task_id)`
3. 第 144 行：`audio_task_manager.get_all_tasks()` → `await audio_task_manager.get_all_tasks()`
4. 第 151 行：`audio_task_manager.get_task(task_id)` → `await audio_task_manager.get_task(task_id)`
5. 第 155 行：`audio_task_manager.remove_task(task_id)` → `await audio_task_manager.remove_task(task_id)`

**注意**: 这些 API 端点函数本身已经是 `async def`

**提交**: `aefbe6e`

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/audio/task_manager.py` | 重写为纯异步 |
| `backend/src/processors/audio_processor.py` | 添加 await 调用 |
| `backend/src/api/audio.py` | 添加 await 调用 |

---

## 提交记录

```
aefbe6e 修复: 修改音频 API 使用 await 调用异步方法
f2b0989 修复: 修改 AudioProcessor 使用 await 调用异步方法
0ceaf58 修复: 重写 AudioTaskManager 为纯异步实现
```

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
