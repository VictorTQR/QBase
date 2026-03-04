# 修复音频去重返回后 task_id 不一致问题

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 修复音频文件去重后返回的 task_id 与后台处理使用的 task_id 不一致的问题。

**架构:**
- `AudioTaskManager.add_task()` 去重时返回 `ParseTask` 对象
- `AudioProcessor.process()` 需要检查返回值类型
- 如果是去重返回，直接返回已有任务信息，不启动后台处理

**技术栈:** FastAPI, SQLAlchemy (async), Python

---

## 前置准备

### 任务 0: 备份当前状态

**文件:**
- 检查: `backend/qbase_parse.db`

**步骤 1: Git 备份**

```bash
git add .
git commit -m "backup: before audio duplicate return fix"
```

---

## 第一阶段：修复 AudioTaskManager.add_task()

### 任务 1: 统一 add_task() 返回类型

**文件:**
- 修改: `backend/src/audio/task_manager.py:116-170`

**步骤 1: 修改 add_task() 返回类型**

当前问题：去重时返回 `ParseTask` 对象，新建时返回 `AudioTaskInfo`，类型不一致。

修改方案：
- 去重时将 `ParseTask` 转换为 `AudioTaskInfo` 返回
- 这样返回类型统一，调用方更容易处理

**修改代码:**

```python
async def add_task(self, task_info: AudioTaskInfo, file_hash: Optional[str] = None):
    """添加音频任务到数据库"""
    import json
    import time

    repo, session = await self._get_repo()
    try:
        # 去重检查
        if file_hash:
            existing = await repo.get_by_hash(file_hash)
            if existing and existing.state == "done":
                logger.info(f"文件已解析，返回已有结果: {existing.id}")
                # 将 ParseTask 转换为 AudioTaskInfo 返回
                return self._parse_task_to_audio_info(existing)

        # ... 现有创建任务的代码 ...
        
        # 创建新任务后也返回 AudioTaskInfo
        task = await repo.create(task_data)
        logger.info(f"添加音频任务到数据库: {task.id}")
        # 将新创建的 ParseTask 转换为 AudioTaskInfo 返回
        return self._parse_task_to_audio_info(task)
    finally:
        await session.close()
```

**步骤 2: 验证修改**

确认文件已正确更新。

**步骤 3: 提交**

```bash
git add backend/src/audio/task_manager.py
git commit -m "fix: unify add_task() return type to AudioTaskInfo"
```

---

## 第二阶段：修复 AudioProcessor.process()

### 任务 2: 修改 process() 检查返回值

**文件:**
- 修改: `backend/src/processors/audio_processor.py:29-59`

**步骤 1: 修改 process() 逻辑**

当前问题：
- 不管 `add_task()` 返回什么，都用新的 `task_id`
- 去重后仍然启动后台处理

修改方案：
1. 检查 `add_task()` 的返回值
2. 如果返回的 task_id 与我们生成的不同，说明是去重返回
3. 直接返回已有任务信息，不启动后台处理

**修改代码:**

```python
async def process(
    self,
    file_path: str,
    config: Optional[dict] = None,
    file_content: Optional[bytes] = None,
) -> dict:
    config = config or {}
    task_id = str(uuid.uuid4())

    # 计算文件 hash
    if file_content:
        file_hash = compute_bytes_hash(file_content)
    else:
        file_hash = await compute_file_hash(file_path)

    logger.debug(f"文件 hash 计算完成: {file_hash}")

    # 创建任务记录
    task = await self._create_task(task_id, file_path, file_hash)

    # 检查是否是去重返回（task_id 不同）
    if task.task_id != task_id:
        logger.info(f"文件已存在，返回已有任务: {task.task_id}")
        # 直接返回已有任务信息，不启动后台处理
        return {
            "task_id": task.task_id,
            "status": task.status,
            "message": "音频转录任务已存在",
        }

    # 启动后台处理（不阻塞请求）
    import asyncio

    asyncio.create_task(self._process_task(task_id, file_path, config))

    return {
        "task_id": task_id,
        "status": AudioTaskStatus.PENDING,
        "message": "音频转录任务已创建",
    }
```

**步骤 2: 验证修改**

确认文件已正确更新。

**步骤 3: 提交**

```bash
git add backend/src/processors/audio_processor.py
git commit -m "fix: check add_task() return value and skip background processing for duplicates"
```

---

## 第三阶段：测试与验证

### 任务 3: 测试验证

**文件:**
- 操作: 手动测试

**步骤 1: 启动后端服务**

```bash
cd backend
python main.py
```

**步骤 2: 验证启动无错误**

检查日志，确认启动成功。

**步骤 3: 测试同一个文件上传两次**

1. 上传同一个音频文件第一次
2. 验证任务创建成功
3. 等待任务完成
4. 上传同一个音频文件第二次
5. 验证第二次返回已有任务的 task_id
6. 验证第二次没有启动后台处理（无错误日志）

**步骤 4: 验证后台处理不启动**

检查日志，确认第二次上传后：
- 没有 `任务不存在` 错误
- 没有启动后台处理任务

---

## 总结

### 修改的文件

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/src/audio/task_manager.py` | 修改 | 统一 add_task() 返回类型为 AudioTaskInfo |
| `backend/src/processors/audio_processor.py` | 修改 | 检查返回值，去重时不启动后台处理 |

### 验证清单

- [x] 后端启动无错误
- [x] 同一个文件第一次上传正常工作
- [x] 同一个文件第二次上传返回已有 task_id
- [x] 第二次上传没有启动后台处理
- [x] 没有"任务不存在"错误

---

Plan complete and saved to `docs/plans/2026-03-04-fix-audio-duplicate-return-bug.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
