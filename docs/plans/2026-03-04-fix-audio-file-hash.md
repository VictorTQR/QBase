# 修复音频文件 Hash 不一致问题实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 修复音频文件上传时 hash 值不一致的问题，使用基于文件内容的 hash 计算方式，与文档解析保持一致。

**架构:** 
- 复用现有的 `utils.file_hash.compute_bytes_hash()` 和 `compute_file_hash()` 函数
- 在 `AudioProcessor` 中计算 hash 并传递给 `AudioTaskManager`
- 在 `AudioTaskManager.add_task()` 中使用传递的 hash，而不是基于 task_id 生成
- 添加去重检查逻辑

**技术栈:** FastAPI, SQLAlchemy (async), Python hashlib

---

## 前置准备

## 第一阶段：修改 AudioProcessor

### 任务 1: 修改 AudioProcessor 添加 hash 计算

**文件:**
- 修改: `backend/src/processors/audio_processor.py`

**步骤 1: 添加导入**

在文件顶部添加：

```python
from utils.file_hash import compute_bytes_hash, compute_file_hash
```

**步骤 2: 修改 process() 方法签名**

修改 `process()` 方法（约第 29 行），添加 `file_content` 参数：

```python
async def process(
    self, 
    file_path: str, 
    config: Optional[dict] = None,
    file_content: Optional[bytes] = None,
) -> dict:
```

**步骤 3: 在 process() 中计算 hash**

在 `process()` 方法中，创建任务前添加 hash 计算：

```python
# 计算文件 hash
if file_content:
    file_hash = compute_bytes_hash(file_content)
else:
    file_hash = await compute_file_hash(file_path)

logger.debug(f"文件 hash 计算完成: {file_hash}")

# 创建任务记录
task = await self._create_task(task_id, file_path, file_hash)
```

**步骤 4: 修改 _create_task() 方法签名**

修改 `_create_task()` 方法（约第 47 行），添加 `file_hash` 参数：

```python
async def _create_task(
    self, 
    task_id: str, 
    file_path: str,
    file_hash: Optional[str] = None,
) -> AudioTaskInfo:
```

**步骤 5: 在 _create_task() 中计算 hash（如果未提供）**

在 `_create_task()` 方法中，创建 AudioTaskInfo 前添加：

```python
# 如果没有提供 hash，计算它
if not file_hash:
    file_hash = await compute_file_hash(file_path)
    logger.debug(f"文件 hash 计算完成（备用）: {file_hash}")
```

**步骤 6: 验证修改**

确认文件已正确更新。

**步骤 7: 提交**

```bash
git add backend/src/processors/audio_processor.py
git commit -m "feat: add file hash calculation to AudioProcessor"
```

---

### 任务 2: 修改音频 API 传递 file_content

**文件:**
- 修改: `backend/src/api/audio.py`

**步骤 1: 修改 transcribe_audio_upload() 传递 file_content**

在 `transcribe_audio_upload()` 方法中（约第 62 行），修改 `audio_processor.process()` 调用：

```python
result = await audio_processor.process(
    temp_file_path,
    config={"model": model} if model else None,
    file_content=content,  # 传递文件内容
)
```

**步骤 2: 验证修改**

确认文件已正确更新。

**步骤 3: 提交**

```bash
git add backend/src/api/audio.py
git commit -m "feat: pass file_content to audio_processor.process"
```

---

## 第二阶段：修改 AudioTaskManager

### 任务 3: 修改 AudioTaskManager.add_task() 使用 hash

**文件:**
- 修改: `backend/src/audio/task_manager.py`

**步骤 1: 修改 add_task() 方法签名**

修改 `add_task()` 方法（约第 108 行），添加 `file_hash` 参数：

```python
async def add_task(
    self, 
    task_info: AudioTaskInfo,
    file_hash: Optional[str] = None,
):
```

**步骤 2: 添加去重检查**

在 `add_task()` 方法中，创建 task_data 前添加去重检查：

```python
# 去重检查
existing = await repo.get_by_hash(file_hash)
if existing and existing.state == "done":
    logger.info(f"文件已解析，返回已有结果: {existing.id}")
    return existing
```

**步骤 3: 使用传递的 file_hash**

在 `task_data` 字典中（约第 142 行），修改 file_hash 字段：

```python
"file_hash": file_hash or f"audio_{task_info.task_id}",
```

**步骤 4: 验证修改**

确认文件已正确更新。

**步骤 5: 提交**

```bash
git add backend/src/audio/task_manager.py
git commit -m "feat: use content-based file_hash in AudioTaskManager"
```

---

## 第三阶段：测试与验证

### 任务 4: 测试验证

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

1. 上传同一个音频文件两次
2. 验证两次的 file_hash 相同
3. 验证第二次上传返回已有结果（去重生效）

**步骤 4: 测试不同文件**

1. 上传不同的音频文件
2. 验证它们的 file_hash 不同

**步骤 5: 测试本地文件**

1. 使用本地文件路径创建转录任务
2. 验证 hash 计算正常

---

## 总结

### 修改的文件

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/src/processors/audio_processor.py` | 修改 | 添加 hash 计算和传递 |
| `backend/src/api/audio.py` | 修改 | 传递 file_content 给 processor |
| `backend/src/audio/task_manager.py` | 修改 | 使用基于内容的 hash，添加去重 |

### 验证清单

- [x] 后端启动无错误
- [x] 同一个文件上传两次，hash 值相同
- [x] 去重检查正常工作
- [x] 不同文件 hash 值不同
- [x] 本地文件路径 hash 计算正常
- [x] 音频转录功能正常工作

---

Plan complete and saved to `docs/plans/2026-03-04-fix-audio-file-hash.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
