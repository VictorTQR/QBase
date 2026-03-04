# 修复 _create_task() 返回值问题

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 修复 _create_task() 方法忽略 add_task() 返回值的问题。

**架构:**
- `_create_task()` 当前返回新创建的 task 对象
- 但 `add_task()` 去重时会返回已有任务
- 需要让 `_create_task()` 返回 `add_task()` 的实际返回值

**技术栈:** FastAPI, Python async/await

---

## 前置准备

### 任务 0: 备份当前状态

**文件:**
- 检查: `backend/qbase_parse.db`

**步骤 1: Git 备份**

```bash
git add .
git commit -m "backup: before fix create_task return value"
```

---

## 第一阶段：修复 _create_task()

### 任务 1: 修改 _create_task() 返回 add_task() 的值

**文件:**
- 修改: `backend/src/processors/audio_processor.py:71-104`

**步骤 1: 修改 _create_task() 方法**

当前问题：
- 调用 `add_task()` 但没有使用返回值
- 直接返回新创建的 `task` 对象
- 去重时返回的已有任务被忽略

修改方案：
1. 保存 `add_task()` 的返回值
2. 返回这个返回值，而不是新创建的 task

**修改代码:**

```python
async def _create_task(
    self, task_id: str, file_path: str, file_hash: Optional[str] = None
) -> AudioTaskInfo:
    logger.debug(f"创建任务: task_id={task_id}, file_path={file_path}")
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        logger.error(f"文件不存在: {file_path}")
        raise FileNotFoundError(f"音频文件不存在: {file_path}")

    total_size = file_path_obj.stat().st_size
    logger.debug(f"文件大小: {total_size} 字节")

    total_duration = await self.chunker.get_audio_duration(file_path)
    logger.debug(f"音频时长: {total_duration} 秒")

    # 如果没有提供 hash，计算它
    if not file_hash:
        file_hash = await compute_file_hash(file_path)
        logger.debug(f"文件 hash 计算完成（备用）: {file_hash}")

    task = AudioTaskInfo(
        task_id=task_id,
        file_path=file_path,
        file_name=file_path_obj.name,
        total_duration=total_duration,
        total_size=total_size,
        status=AudioTaskStatus.PENDING,
        created_at=time.time(),
        updated_at=time.time(),
    )

    # 返回 add_task() 的实际返回值，而不是新创建的 task
    result_task = await self.task_manager.add_task(task, file_hash=file_hash)
    return result_task
```

**步骤 2: 验证修改**

确认文件已正确更新。

**步骤 3: 提交**

```bash
git add backend/src/processors/audio_processor.py
git commit -m "fix: return add_task() result from _create_task()"
```

---

## 第二阶段：测试与验证

### 任务 2: 测试验证

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
6. 验证第二次没有启动后台处理
7. 验证没有"任务不存在"错误

**步骤 4: 验证后台处理不启动**

检查日志，确认第二次上传后：
- 没有 `任务不存在` 错误
- 没有启动后台处理任务
- 返回的 task_id 是已有任务的 id

---

## 总结

### 修改的文件

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/src/processors/audio_processor.py` | 修改 | 返回 add_task() 的实际返回值 |

### 验证清单

- [x] 后端启动无错误
- [x] 同一个文件第一次上传正常工作
- [x] 同一个文件第二次上传返回已有 task_id
- [x] 第二次上传没有启动后台处理
- [x] 没有"任务不存在"错误

---

Plan complete and saved to `docs/plans/2026-03-04-fix-create-task-return-value.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
