# 统一数据存储重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 扩展现有的 ParseTask 表结构，统一文档解析和音频转录的数据存储，优化向量索引流程。

**架构:** 
- 扩展现有的 parse_tasks 表，增加 file_type 和 metadata 字段
- 音频任务从内存存储迁移到 SQLite 数据库
- 向量索引支持通过 task_id 从数据库获取内容，避免传输大文本

**技术栈:** FastAPI, SQLAlchemy (async), SQLite, Vue 3, Pinia

---

## 前置准备

### 任务 0: 备份当前状态

**文件:**
- 检查: `backend/qbase_parse.db`

**步骤 1: 删除旧数据库**

```bash
# 删除旧的数据库文件，让系统重建
rm backend/qbase_parse.db
```

**步骤 2: Git 备份**

```bash
git add .
git commit -m "backup: before unified storage refactor"
```

---

## 第一阶段：数据库层重构

### 任务 1: 扩展 ParseTask 数据模型

**文件:**
- 修改: `backend/src/models/db_models.py`

**步骤 1: 修改 db_models.py**

用以下内容替换现有内容：

```python
from sqlalchemy import Column, String, Integer, Text
from database import Base


class ParseTask(Base):
    __tablename__ = "parse_tasks"

    id = Column(String, primary_key=True, index=True)
    batch_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    file_size = Column(Integer, nullable=True)
    parser_type = Column(String, nullable=False, default="mineru", index=True)
    file_type = Column(String, nullable=False, default="document", index=True)
    state = Column(String, nullable=False, index=True)
    error_msg = Column(Text, nullable=True)
    markdown_content = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)
    result_file_path = Column(String, nullable=True)
    result_file_format = Column(String, nullable=True, default="zip")
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
```

**步骤 2: 验证修改**

确认文件已正确更新。

**步骤 3: 提交**

```bash
git add backend/src/models/db_models.py
git commit -m "refactor: extend ParseTask with file_type and metadata"
```

---

### 任务 2: 扩展 ParseTaskRepository

**文件:**
- 修改: `backend/src/repositories/parse_task_repository.py`

**步骤 1: 添加新方法**

在文件末尾添加以下方法：

```python
    async def list_by_type(self, file_type: str, limit: int = 100, offset: int = 0) -> List[ParseTask]:
        """按文件类型列出任务"""
        result = await self.db.execute(
            select(ParseTask)
            .where(ParseTask.file_type == file_type)
            .order_by(desc(ParseTask.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_stats_by_type(self, file_type: str) -> Dict[str, Any]:
        """按文件类型获取统计"""
        from sqlalchemy import func
        
        total_result = await self.db.execute(
            select(func.count(ParseTask.id)).where(ParseTask.file_type == file_type)
        )
        total = total_result.scalar()

        states = ["pending", "running", "done", "failed"]
        stats = {"total": total or 0}

        for state in states:
            result = await self.db.execute(
                select(func.count(ParseTask.id))
                .where(ParseTask.file_type == file_type)
                .where(ParseTask.state == state)
            )
            stats[state] = result.scalar() or 0

        return stats
```

同时需要在文件顶部添加 `desc` 的导入（如果没有）：

```python
from sqlalchemy import select, desc, func
```

**步骤 2: 更新 _task_to_dict 方法（在 mineru/task_manager.py 中）**

注意：这个步骤在后面的任务中处理。

**步骤 3: 提交**

```bash
git add backend/src/repositories/parse_task_repository.py
git commit -m "refactor: add list_by_type and get_stats_by_type to repository"
```

---

## 第二阶段：音频模块重构

### 任务 3: 重写音频任务管理器

**文件:**
- 重写: `backend/src/audio/task_manager.py`

**步骤 1: 完全重写 task_manager.py**

用以下内容替换现有内容：

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository
from utils.websocket_manager import websocket_manager
from models.audio_schemas import AudioTaskInfo, AudioTaskStatus, AudioChunkInfo


class AudioTaskManager:
    """音频任务管理器（数据库存储）"""

    _instance: Optional["AudioTaskManager"] = None
    _lock = None

    def __new__(cls):
        import threading
        if cls._instance is None:
            cls._lock = threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    async def _get_repo(self):
        """获取数据库会话和 repository"""
        session = AsyncSessionLocal()
        return ParseTaskRepository(session), session

    def _map_status_to_state(self, status: AudioTaskStatus) -> str:
        """将音频状态映射为统一状态"""
        status_map = {
            AudioTaskStatus.PENDING: "pending",
            AudioTaskStatus.PROCESSING: "running",
            AudioTaskStatus.CHUNKING: "running",
            AudioTaskStatus.TRANSCRIBING: "running",
            AudioTaskStatus.MERGING: "running",
            AudioTaskStatus.COMPLETED: "done",
            AudioTaskStatus.FAILED: "failed",
        }
        return status_map.get(status, "pending")

    def _map_state_to_status(self, state: str) -> AudioTaskStatus:
        """将统一状态映射为音频状态"""
        state_map = {
            "pending": AudioTaskStatus.PENDING,
            "running": AudioTaskStatus.PROCESSING,
            "done": AudioTaskStatus.COMPLETED,
            "failed": AudioTaskStatus.FAILED,
        }
        return state_map.get(state, AudioTaskStatus.PENDING)

    def _parse_task_to_audio_info(self, task) -> AudioTaskInfo:
        """将数据库 ParseTask 转换为 AudioTaskInfo"""
        import json
        metadata = {}
        if task.metadata:
            try:
                metadata = json.loads(task.metadata)
            except:
                pass

        status = self._map_state_to_status(task.state)
        chunks = metadata.get("chunks", [])
        chunk_infos = []
        for chunk_data in chunks:
            chunk_infos.append(AudioChunkInfo(
                chunk_id=chunk_data.get("chunk_id", ""),
                file_path=chunk_data.get("file_path", ""),
                start_time=chunk_data.get("start_time", 0),
                end_time=chunk_data.get("end_time", 0),
                duration=chunk_data.get("duration", 0),
                status=self._map_state_to_status(chunk_data.get("status", "pending")),
                transcription=chunk_data.get("transcription"),
                error=chunk_data.get("error"),
            ))

        return AudioTaskInfo(
            task_id=task.id,
            file_path=task.file_path or "",
            file_name=task.file_name,
            total_duration=metadata.get("total_duration", 0),
            total_size=task.file_size or 0,
            status=status,
            chunks=chunk_infos,
            transcription=task.markdown_content,
            error=task.error_msg,
            created_at=metadata.get("created_at_timestamp", 0),
            updated_at=metadata.get("updated_at_timestamp", 0),
        )

    async def add_task(self, task_info: AudioTaskInfo):
        """添加音频任务到数据库"""
        import json
        import time

        repo, session = await self._get_repo()
        try:
            metadata = {
                "total_duration": task_info.total_duration,
                "chunk_count": len(task_info.chunks),
                "chunks": [],
                "created_at_timestamp": task_info.created_at,
                "updated_at_timestamp": task_info.updated_at,
            }

            for chunk in task_info.chunks:
                metadata["chunks"].append({
                    "chunk_id": chunk.chunk_id,
                    "file_path": chunk.file_path,
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                    "duration": chunk.duration,
                    "status": chunk.status.value,
                    "transcription": chunk.transcription,
                    "error": chunk.error,
                })

            task_data = {
                "id": task_info.task_id,
                "batch_id": f"audio_{int(time.time())}",
                "file_name": task_info.file_name,
                "file_path": task_info.file_path,
                "file_hash": f"audio_{task_info.task_id}",
                "file_size": task_info.total_size,
                "parser_type": "siliconflow_asr",
                "file_type": "audio",
                "state": self._map_status_to_state(task_info.status),
                "error_msg": task_info.error,
                "markdown_content": task_info.transcription,
                "metadata": json.dumps(metadata, ensure_ascii=False),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            task = await repo.create(task_data)
            logger.info(f"添加音频任务到数据库: {task.id}")
            return task
        finally:
            await session.close()

    def get_task(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取音频任务（同步包装）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在事件循环中，创建任务
                task = asyncio.create_task(self._get_task_async(task_id))
                return loop.run_until_complete(task)
            else:
                return loop.run_until_complete(self._get_task_async(task_id))
        except RuntimeError:
            # 如果没有事件循环，创建新的
            import asyncio
            return asyncio.run(self._get_task_async(task_id))

    async def _get_task_async(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取音频任务（异步实现）"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_id(task_id)
            if task and task.file_type == "audio":
                return self._parse_task_to_audio_info(task)
            return None
        finally:
            await session.close()

    def update_task(self, task_info: AudioTaskInfo):
        """更新音频任务（同步包装）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self._update_task_async(task_info))
                return loop.run_until_complete(task)
            else:
                return loop.run_until_complete(self._update_task_async(task_info))
        except RuntimeError:
            import asyncio
            return asyncio.run(self._update_task_async(task_info))

    async def _update_task_async(self, task_info: AudioTaskInfo):
        """更新音频任务（异步实现）"""
        import json
        repo, session = await self._get_repo()
        try:
            metadata = {
                "total_duration": task_info.total_duration,
                "chunk_count": len(task_info.chunks),
                "chunks": [],
                "created_at_timestamp": task_info.created_at,
                "updated_at_timestamp": task_info.updated_at,
            }

            for chunk in task_info.chunks:
                metadata["chunks"].append({
                    "chunk_id": chunk.chunk_id,
                    "file_path": chunk.file_path,
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                    "duration": chunk.duration,
                    "status": chunk.status.value if hasattr(chunk.status, 'value') else str(chunk.status),
                    "transcription": chunk.transcription,
                    "error": chunk.error,
                })

            updates = {
                "state": self._map_status_to_state(task_info.status),
                "error_msg": task_info.error,
                "markdown_content": task_info.transcription,
                "metadata": json.dumps(metadata, ensure_ascii=False),
            }

            task = await repo.update(task_info.task_id, updates)
            
            # WebSocket 广播
            try:
                asyncio.create_task(
                    websocket_manager.broadcast_task_update(
                        "audio",
                        {
                            "type": "task_update",
                            "task_id": task_info.task_id,
                            "task_type": "audio",
                            "state": self._map_status_to_state(task_info.status),
                            "data": {
                                "task_id": task_info.task_id,
                                "status": task_info.status.value if hasattr(task_info.status, 'value') else str(task_info.status),
                                "file_name": task_info.file_name,
                            },
                        },
                    )
                )
            except Exception as e:
                logger.error(f"Failed to broadcast audio task update: {e}")

            return task
        finally:
            await session.close()

    def remove_task(self, task_id: str):
        """删除音频任务（同步包装）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self._remove_task_async(task_id))
                loop.run_until_complete(task)
            else:
                loop.run_until_complete(self._remove_task_async(task_id))
        except RuntimeError:
            import asyncio
            asyncio.run(self._remove_task_async(task_id))

    async def _remove_task_async(self, task_id: str):
        """删除音频任务（异步实现）"""
        repo, session = await self._get_repo()
        try:
            from sqlalchemy import delete
            await self.db.execute(delete(ParseTask).where(ParseTask.id == task_id))
            await self.db.commit()
            logger.info(f"删除音频任务: {task_id}")
        finally:
            await session.close()

    def get_all_tasks(self) -> Dict[str, AudioTaskInfo]:
        """获取所有音频任务（同步包装）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self._get_all_tasks_async())
                return loop.run_until_complete(task)
            else:
                return loop.run_until_complete(self._get_all_tasks_async())
        except RuntimeError:
            import asyncio
            return asyncio.run(self._get_all_tasks_async())

    async def _get_all_tasks_async(self) -> Dict[str, AudioTaskInfo]:
        """获取所有音频任务（异步实现）"""
        repo, session = await self._get_repo()
        try:
            tasks = await repo.list_by_type("audio", limit=1000)
            result = {}
            for task in tasks:
                result[task.id] = self._parse_task_to_audio_info(task)
            return result
        finally:
            await session.close()


# 全局单例实例
audio_task_manager = AudioTaskManager()
```

**步骤 2: 验证文件**

确认文件已完全重写。

**步骤 3: 提交**

```bash
git add backend/src/audio/task_manager.py
git commit -m "refactor: rewrite AudioTaskManager to use database storage"
```

---

### 任务 4: 适配音频处理器

**文件:**
- 修改: `backend/src/processors/audio_processor.py`

**步骤 1: 检查并修复导入**

确认导入语句正确，不需要修改（因为 AudioTaskManager 接口保持兼容）。

**步骤 2: 验证无需修改**

由于 AudioTaskManager 的公共接口保持不变，这个文件应该不需要修改。

**步骤 3: 提交（如果有修改）**

如果没有修改，跳过提交。

---

### 任务 5: 适配音频 API

**文件:**
- 修改: `backend/src/api/audio.py`

**步骤 1: 验证 API 无需修改**

由于 AudioTaskManager 接口保持兼容，这个文件应该不需要修改。

**步骤 2: 测试确认**

（后面的测试阶段验证）

---

## 第三阶段：文档模块适配

### 任务 6: 更新文档任务管理器

**文件:**
- 修改: `backend/src/mineru/task_manager.py`

**步骤 1: 修改 _task_to_dict 方法**

更新 `_task_to_dict` 方法（约第 192 行），添加新字段：

```python
    def _task_to_dict(self, task) -> Dict[str, Any]:
        """将数据库模型转换为字典"""
        return {
            "id": task.id,
            "batch_id": task.batch_id,
            "file_name": task.file_name,
            "file_path": task.file_path,
            "file_hash": task.file_hash,
            "state": task.state,
            "error_msg": task.error_msg,
            "markdown_content": task.markdown_content,
            "result_file_path": task.result_file_path,
            "result_file_format": task.result_file_format,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "file_type": getattr(task, "file_type", "document"),
            "metadata": getattr(task, "metadata", None),
        }
```

**步骤 2: 修改 create_task 方法**

在 `create_task` 方法中（约第 68 行），添加新字段：

```python
        task_data = {
            "id": task_id,
            "batch_id": batch_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "parser_type": "mineru",
            "file_type": "document",
            "state": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
```

**步骤 3: 提交**

```bash
git add backend/src/mineru/task_manager.py
git commit -m "refactor: add file_type to mineru task manager"
```

---

## 第四阶段：向量索引优化

### 任务 7: 扩展向量索引 Schema

**文件:**
- 修改: `backend/src/vector/schemas.py`

**步骤 1: 修改 VectorIndexRequest**

更新 `VectorIndexRequest` 类：

```python
class VectorIndexRequest(BaseModel):
    file_path: str
    file_name: str
    content: Optional[str] = None
    task_id: Optional[str] = None
    workspace_id: Optional[str] = None
    content_type: Optional[str] = "text"
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
```

注意：`content` 现在是可选的。

**步骤 2: 提交**

```bash
git add backend/src/vector/schemas.py
git commit -m "refactor: add task_id to VectorIndexRequest, make content optional"
```

---

### 任务 8: 修改向量索引 API

**文件:**
- 修改: `backend/src/api/vector.py`

**步骤 1: 添加导入**

在文件顶部添加：

```python
from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository
```

**步骤 2: 修改 index_document 函数**

替换整个 `index_document` 函数（约第 23-105 行）：

```python
@router.post("/index", response_model=VectorIndexResponse)
async def index_document(request: Request):
    """索引单个文档"""
    try:
        body = await request.json()
        logger.info(f"[Vector API] 收到索引请求，原始请求体: {body}")
        logger.info(f"[Vector API] file_path: {body.get('file_path')}")
        logger.info(f"[Vector API] file_name: {body.get('file_name')}")
        logger.info(f"[Vector API] task_id: {body.get('task_id')}")
        logger.info(f"[Vector API] content 长度: {len(body.get('content', '')) if body.get('content') else 'N/A'}")
        
        try:
            validated_request = VectorIndexRequest(**body)
            logger.info(f"[Vector API] Pydantic 验证通过")
        except ValidationError as e:
            logger.error(f"[Vector API] Pydantic 验证失败: {e.errors()}")
            raise HTTPException(
                status_code=422,
                detail={"error": "Validation failed", "details": e.errors()},
            )

        # 获取内容：优先从 task_id 获取，其次使用请求中的 content
        content = validated_request.content
        if validated_request.task_id:
            logger.info(f"[Vector API] 从数据库获取内容，task_id: {validated_request.task_id}")
            repo, session = AsyncSessionLocal(), None
            try:
                session = AsyncSessionLocal()
                repo = ParseTaskRepository(session)
                task = await repo.get_by_id(validated_request.task_id)
                if task and task.markdown_content:
                    content = task.markdown_content
                    logger.info(f"[Vector API] 从数据库获取内容成功，长度: {len(content)}")
                else:
                    logger.warning(f"[Vector API] 无法从数据库获取内容，task_id: {validated_request.task_id}")
            except Exception as e:
                logger.error(f"[Vector API] 从数据库获取内容失败: {e}")
            finally:
                if session:
                    await session.close()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Either content or task_id with valid content is required"
            )

        chunk_size = validated_request.chunk_size or settings.VECTOR_CHUNK_SIZE
        chunk_overlap = validated_request.chunk_overlap or settings.VECTOR_CHUNK_OVERLAP

        logger.info(
            f"[Vector API] 使用 chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
        )

        chunks = TextChunker.chunk(
            content,
            {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "use_semantic": True,
            },
        )

        logger.info(f"[Vector API] 文本分块完成，共 {len(chunks)} 个分块")

        indexed_chunks = []
        for idx, chunk in enumerate(chunks):
            logger.info(f"[Vector API] 正在处理第 {idx + 1}/{len(chunks)} 个分块")
            embedding = await EmbeddingService.embed_text(
                chunk["content"], settings.SILICONFLOW_EMBEDDING_MODEL
            )

            chunk_id = f"{validated_request.file_path}_chunk_{chunk['index']}"
            indexed_chunks.append(
                {
                    "id": chunk_id,
                    "file_path": validated_request.file_path,
                    "file_name": validated_request.file_name,
                    "workspace_id": validated_request.workspace_id or "",
                    "chunk_index": chunk["index"],
                    "content_type": validated_request.content_type or "text",
                    "content": chunk["content"],
                    "start_char": chunk["start_char"],
                    "end_char": chunk["end_char"],
                    "vector": embedding,
                }
            )

        logger.info(f"[Vector API] 准备删除旧索引: {validated_request.file_path}")
        lancedb_service.delete_by_file_path(validated_request.file_path)
        logger.info(f"[Vector API] 准备添加新索引，共 {len(indexed_chunks)} 个分块")
        lancedb_service.add_chunks(indexed_chunks)
        logger.info(f"[Vector API] 索引添加成功")

        return VectorIndexResponse(
            success=True,
            chunks_indexed=len(indexed_chunks),
            message=f"Successfully indexed {len(indexed_chunks)} chunks",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Vector API] 索引文档时发生异常")
        raise HTTPException(status_code=500, detail=str(e))
```

**步骤 3: 提交**

```bash
git add backend/src/api/vector.py
git commit -m "refactor: support indexing by task_id from database"
```

---

## 第五阶段：前端适配

### 任务 9: 修改前端向量 Store

**文件:**
- 修改: `app/src/stores/vector.js`

**步骤 1: 修改 indexDocument 函数**

更新 `indexDocument` 函数签名和实现：

```javascript
    async function indexDocument(filePath, fileName, content, workspaceId, taskId) {
      isIndexing.value = true
      currentIndexingFile.value = fileName
      error.value = null

      const requestParams = {
        file_path: filePath,
        file_name: fileName,
        workspace_id: workspaceId || '',
      }

      if (taskId) {
        requestParams.task_id = taskId
        console.log('[VectorStore] 使用 task_id 索引:', taskId)
      } else {
        requestParams.content = content
        console.log('[VectorStore] 使用 content 索引，长度:', content?.length || 0)
      }

      console.log('[VectorStore] 准备索引文档，请求参数:', requestParams)
      console.log('[VectorStore] workspace_id (处理后):', requestParams.workspace_id)

      try {
        const result = await VectorBackendApi.indexDocument(requestParams)
        console.log('[VectorStore] 索引成功:', result)
        indexedFiles.value[filePath] = true
        await loadStats()
        return result
      } catch (err) {
        console.error('[VectorStore] 索引失败:', err)
        console.error('[VectorStore] 错误详情:', {
          message: err.message,
          response: err.response,
          status: err.status,
        })
        error.value = err.message
        throw err
      } finally {
        isIndexing.value = false
        currentIndexingFile.value = ''
      }
    }
```

**步骤 2: 修改 indexBatch 函数**

更新 `indexBatch` 函数中的调用：

```javascript
    async function indexBatch(tasks, getExtractedTextFn, workspaceId = null) {
      isIndexing.value = true
      indexingProgress.value = 0
      indexingTotal.value = tasks.length
      error.value = null
      const results = []
      const failed = []

      try {
        for (let i = 0; i < tasks.length; i++) {
          const task = tasks[i]
          currentIndexingFile.value = task.file_name
          indexingProgress.value = i + 1

          try {
            const result = await indexDocument(
              task.file_path,
              task.file_name,
              null,
              workspaceId,
              task.id,
            )
            results.push({ task, result })
          } catch (err) {
            failed.push({ task, error: err.message })
          }
        }

        await loadStats()
        return { success: true, results, failed }
      } catch (err) {
        error.value = err.message
        throw err
      } finally {
        isIndexing.value = false
        indexingProgress.value = 0
        indexingTotal.value = 0
        currentIndexingFile.value = ''
      }
    }
```

注意：移除了 `getExtractedTextFn` 的调用，直接传 `task.id`。

**步骤 3: 提交**

```bash
git add app/src/stores/vector.js
git commit -m "refactor: support taskId parameter in vector store"
```

---

### 任务 10: 修改前端解析页面

**文件:**
- 修改: `app/src/components/parse/ParseDocumentsView.vue`

**步骤 1: 修改 handleIndexDocument 函数**

更新函数（约第 134-147 行）：

```javascript
async function handleIndexDocument(task) {
  try {
    await vectorStore.indexDocument(
      task.file_path, 
      task.file_name, 
      null, 
      null,
      task.id
    )
    ElMessage.success(`已成功索引 ${task.file_name}`)
  } catch (err) {
    ElMessage.error(`索引失败: ${err.message}`)
  }
}
```

**步骤 2: 修改 handleBatchIndex 函数**

更新函数（约第 149-173 行）：

```javascript
async function handleBatchIndex() {
  if (doneTasksWithoutIndex.value.length === 0) {
    ElMessage.warning('没有需要索引的文档')
    return
  }

  try {
    const result = await vectorStore.indexBatch(
      doneTasksWithoutIndex.value,
      null,
      null,
    )

    if (result.failed.length > 0) {
      ElMessage.warning(`成功索引 ${result.results.length} 个文档，失败 ${result.failed.length} 个`)
    } else {
      ElMessage.success(`成功索引 ${result.results.length} 个文档`)
    }
  } catch (err) {
    ElMessage.error(`批量索引失败: ${err.message}`)
  }
}
```

**步骤 3: 提交**

```bash
git add app/src/components/parse/ParseDocumentsView.vue
git commit -m "refactor: use taskId instead of content for vector indexing"
```

---

## 第六阶段：测试与验证

### 任务 11: 删除旧数据库并测试

**文件:**
- 操作: `backend/qbase_parse.db`

**步骤 1: 删除旧数据库**

```bash
rm backend/qbase_parse.db
```

**步骤 2: 启动后端服务**

```bash
cd backend
python main.py
```

**步骤 3: 验证启动无错误**

检查日志，确认数据库初始化成功，无错误。

**步骤 4: 测试文档解析**

1. 打开前端应用
2. 添加一个 PDF 文档到解析
3. 验证解析完成
4. 验证数据存储到 parse_tasks 表，file_type = "document"

**步骤 5: 测试音频转录**

1. 添加一个音频文件到解析
2. 验证转录完成
3. 验证数据存储到 parse_tasks 表，file_type = "audio"
4. 重启后端，验证音频任务不丢失

**步骤 6: 测试向量索引**

1. 对已解析的文档点击"索引向量"
2. 验证网络请求中只有 task_id，没有大文本 content
3. 验证索引成功

---

## 总结

### 完成的修改

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/src/models/db_models.py` | 修改 | 扩展 ParseTask 表，添加 file_type 和 metadata |
| `backend/src/repositories/parse_task_repository.py` | 修改 | 添加按类型查询和统计方法 |
| `backend/src/audio/task_manager.py` | 重写 | 改用数据库存储 |
| `backend/src/mineru/task_manager.py` | 修改 | 添加 file_type 字段 |
| `backend/src/vector/schemas.py` | 修改 | 添加 task_id，content 可选 |
| `backend/src/api/vector.py` | 修改 | 支持通过 task_id 获取内容 |
| `app/src/stores/vector.js` | 修改 | 支持 taskId 参数 |
| `app/src/components/parse/ParseDocumentsView.vue` | 修改 | 使用 taskId 索引 |

### 验证清单

- [ ] 后端启动无错误
- [ ] 文档解析正常工作
- [ ] 音频转录正常工作且持久化
- [ ] 向量索引通过 task_id 工作
- [ ] WebSocket 实时更新正常
