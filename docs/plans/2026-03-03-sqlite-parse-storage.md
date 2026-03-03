# SQLite 解析结果存储实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 在后端使用 SQLite 存储解析结果，通过文件哈希去重，完全移除前端存储。

**架构：** 混合存储方案 - SQLite 存储元数据和 Markdown 内容，文件系统存储结果文件（支持多种格式）。通过 SHA-256 文件哈希实现去重，完全移除前端 LocalStorage/IndexedDB 存储。

**技术栈：** SQLite + SQLAlchemy (ORM) + FastAPI + Vue 3

---

## 前期准备

### Task 0: 查看后端项目结构

**Files:**
- Read: `backend/pyproject.toml`
- Read: `backend/src/mineru/task_manager.py`

**Step 1:** 读取 pyproject.toml 确认当前依赖

**Step 2:** 读取 task_manager.py 了解当前任务管理实现

---

## 第一阶段：后端数据库集成

### Task 1: 添加数据库依赖

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1:** 在 pyproject.toml 的 dependencies 中添加 SQLAlchemy 和 aiosqlite

```toml
dependencies = [
    "fastapi[uvicorn]>=0.135.1",
    "loguru>=0.7.3",
    "uvicorn>=0.41.0",
    "httpx>=0.27.0",
    "python-multipart>=0.0.9",
    "aiofiles>=24.1.0",
    "python-dotenv>=1.0.0",
    "pydantic-settings>=2.0.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
]
```

**Step 2:** 提交

```bash
git add backend/pyproject.toml
git commit -m "feat: add sqlalchemy and aiosqlite dependencies"
```

---

### Task 2: 创建数据库配置和连接管理

**Files:**
- Create: `backend/src/database.py`
- Modify: `backend/src/config.py`

**Step 1:** 修改 config.py 添加数据库配置

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./qbase_parse.db"
    
    class Config:
        env_file = ".env"
```

**Step 2:** 创建 database.py - SQLAlchemy 异步引擎和会话管理

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建基类
Base = declarative_base()


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库初始化完成")


async def get_db():
    """获取数据库会话的依赖项"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Step 3:** 提交

```bash
git add backend/src/config.py backend/src/database.py
git commit -m "feat: add database configuration and connection management"
```

---

### Task 3: 创建数据库模型

**Files:**
- Create: `backend/src/models/db_models.py`

**Step 1:** 创建 db_models.py 定义 ParseTask 模型

```python
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from datetime import datetime

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
    state = Column(String, nullable=False, index=True)  # pending, running, done, failed
    error_msg = Column(Text, nullable=True)
    markdown_content = Column(Text, nullable=True)
    result_file_path = Column(String, nullable=True)
    result_file_format = Column(String, nullable=True, default="zip")
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
```

**Step 2:** 提交

```bash
git add backend/src/models/db_models.py
git commit -m "feat: add ParseTask database model"
```

---

### Task 4: 创建文件哈希工具

**Files:**
- Create: `backend/src/utils/file_hash.py`

**Step 1:** 创建 file_hash.py 实现 SHA-256 文件哈希计算

```python
import hashlib
from pathlib import Path
from typing import Union
from loguru import logger


async def compute_file_hash(file_path: Union[str, Path]) -> str:
    """计算文件的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()
    
    async with open(file_path, "rb") as f:
        # 分块读取文件，避免大文件内存溢出
        chunk_size = 8192
        while chunk := await f.read(chunk_size):
            sha256_hash.update(chunk)
    
    file_hash = sha256_hash.hexdigest()
    logger.debug(f"文件 {file_path} 哈希: {file_hash}")
    return file_hash


def compute_bytes_hash(content: bytes) -> str:
    """计算字节内容的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()
```

**Step 2:** 修正 - 使用 aiofiles 进行异步文件读取

```python
import hashlib
from pathlib import Path
from typing import Union
import aiofiles
from loguru import logger


async def compute_file_hash(file_path: Union[str, Path]) -> str:
    """计算文件的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()
    
    async with aiofiles.open(file_path, "rb") as f:
        # 分块读取文件，避免大文件内存溢出
        chunk_size = 8192
        while chunk := await f.read(chunk_size):
            sha256_hash.update(chunk)
    
    file_hash = sha256_hash.hexdigest()
    logger.debug(f"文件 {file_path} 哈希: {file_hash}")
    return file_hash


def compute_bytes_hash(content: bytes) -> str:
    """计算字节内容的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()
```

**Step 3:** 提交

```bash
git add backend/src/utils/file_hash.py
git commit -m "feat: add file hash utility functions"
```

---

### Task 5: 创建 Repository 数据访问层

**Files:**
- Create: `backend/src/repositories/parse_task_repository.py`

**Step 1:** 创建 parse_task_repository.py 实现数据访问方法

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.db_models import ParseTask


class ParseTaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, task_data: Dict[str, Any]) -> ParseTask:
        """创建新的解析任务"""
        task = ParseTask(**task_data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        logger.info(f"创建解析任务: {task.id}")
        return task

    async def get_by_id(self, task_id: str) -> Optional[ParseTask]:
        """通过 ID 获取任务"""
        result = await self.db.execute(select(ParseTask).where(ParseTask.id == task_id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, file_hash: str) -> Optional[ParseTask]:
        """通过文件哈希获取任务（用于去重检查）"""
        result = await self.db.execute(select(ParseTask).where(ParseTask.file_hash == file_hash))
        return result.scalar_one_or_none()

    async def update(self, task_id: str, updates: Dict[str, Any]) -> Optional[ParseTask]:
        """更新任务"""
        task = await self.get_by_id(task_id)
        if not task:
            return None
        
        updates["updated_at"] = datetime.now().isoformat()
        for key, value in updates.items():
            setattr(task, key, value)
        
        await self.db.commit()
        await self.db.refresh(task)
        logger.info(f"更新任务 {task_id}: {updates.keys()}")
        return task

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ParseTask]:
        """列出所有任务（分页）"""
        result = await self.db.execute(
            select(ParseTask)
            .order_by(desc(ParseTask.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_state(self, state: str, limit: int = 100) -> List[ParseTask]:
        """按状态列出任务"""
        result = await self.db.execute(
            select(ParseTask)
            .where(ParseTask.state == state)
            .order_by(desc(ParseTask.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self) -> Dict[str, Any]:
        """获取解析统计"""
        # 总数
        total_result = await self.db.execute(select(func.count(ParseTask.id)))
        total = total_result.scalar()
        
        # 按状态统计
        states = ["pending", "running", "done", "failed"]
        stats = {"total": total or 0}
        
        for state in states:
            result = await self.db.execute(
                select(func.count(ParseTask.id)).where(ParseTask.state == state)
            )
            stats[state] = result.scalar() or 0
        
        return stats
```

**Step 2:** 添加 func 导入

```python
from sqlalchemy import select, desc, func
```

**Step 3:** 提交

```bash
git add backend/src/repositories/parse_task_repository.py
git commit -m "feat: add ParseTaskRepository data access layer"
```

---

### Task 6: 重构 TaskManager 使用 SQLite

**Files:**
- Modify: `backend/src/mineru/task_manager.py`

**Step 1:** 完全重写 task_manager.py 使用数据库存储

```python
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from pathlib import Path
from loguru import logger

from config import settings
from mineru.client import mineru_client
from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository
from utils.file_hash import compute_bytes_hash, compute_file_hash


class TaskManager:
    def __init__(self):
        pass

    async def _get_repo(self):
        """获取数据库会话和 repository"""
        session = AsyncSessionLocal()
        return ParseTaskRepository(session), session

    async def check_duplicate(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """检查文件是否已解析（去重检查）"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_hash(file_hash)
            if task and task.state == "done":
                return self._task_to_dict(task)
            return None
        finally:
            await session.close()

    async def create_task(
        self,
        batch_id: str,
        file_name: str,
        file_content: Optional[bytes] = None,
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建解析任务"""
        # 计算文件哈希
        if not file_hash:
            if file_content:
                file_hash = compute_bytes_hash(file_content)
            elif file_path:
                file_hash = await compute_file_hash(file_path)
            else:
                raise ValueError("必须提供 file_content 或 file_path")

        # 检查是否已存在
        existing = await self.check_duplicate(file_hash)
        if existing:
            logger.info(f"文件已解析，返回已有结果: {existing['id']}")
            return existing

        # 计算文件大小
        file_size = None
        if file_content:
            file_size = len(file_content)
        elif file_path:
            file_size = Path(file_path).stat().st_size

        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "batch_id": batch_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "parser_type": "mineru",
            "state": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        repo, session = await self._get_repo()
        try:
            task = await repo.create(task_data)
            return self._task_to_dict(task)
        finally:
            await session.close()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_id(task_id)
            return self._task_to_dict(task) if task else None
        finally:
            await session.close()

    async def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """更新任务"""
        repo, session = await self._get_repo()
        try:
            task = await repo.update(task_id, kwargs)
            return self._task_to_dict(task) if task else None
        finally:
            await session.close()

    async def list_tasks(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出所有任务"""
        repo, session = await self._get_repo()
        try:
            tasks = await repo.list_all(limit, offset)
            return [self._task_to_dict(task) for task in tasks]
        finally:
            await session.close()

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        repo, session = await self._get_repo()
        try:
            return await repo.get_stats()
        finally:
            await session.close()

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
        }

    async def poll_task_status(self, task_id: str) -> None:
        """轮询任务状态（保持原有逻辑）"""
        task = await self.get_task(task_id)
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        await self.update_task(task_id, state="running")

        for attempt in range(settings.MAX_POLL_ATTEMPTS):
            try:
                result = await mineru_client.batch_query_results(task["batch_id"])

                if "extract_result" not in result or len(result["extract_result"]) == 0:
                    await asyncio.sleep(settings.TASK_POLL_INTERVAL)
                    continue

                file_result = result["extract_result"][0]
                state = file_result.get("state")

                logger.info(f"任务 {task_id} 状态: {state}")

                if state == "done":
                    await self.update_task(task_id, state="done")
                    logger.info(f"任务 {task_id} 完成")
                    return
                elif state == "failed":
                    err_msg = file_result.get("err_msg", "任务执行失败")
                    await self.update_task(task_id, state="failed", error_msg=err_msg)
                    logger.error(f"任务 {task_id} 失败: {err_msg}")
                    return
                elif state == "running" and file_result.get("extract_progress"):
                    progress = file_result["extract_progress"]
                    logger.info(
                        f"解析进度: {progress.get('extracted_pages', 0)}/{progress.get('total_pages', 0)} 页"
                    )

            except Exception as e:
                logger.error(f"轮询任务 {task_id} 出错: {str(e)}")
                await self.update_task(task_id, state="failed", error_msg=str(e))
                return

            await asyncio.sleep(settings.TASK_POLL_INTERVAL)

        await self.update_task(task_id, state="failed", error_msg="任务超时")
        logger.error(f"任务 {task_id} 超时")


task_manager = TaskManager()
```

**Step 2:** 提交

```bash
git add backend/src/mineru/task_manager.py
git commit -m "refactor: rewrite TaskManager to use SQLite database"
```

---

### Task 7: 初始化数据库并更新 main.py

**Files:**
- Modify: `backend/main.py`

**Step 1:** 在 main.py 中添加数据库初始化

```python
# 在 startup_event 中添加
@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    logger.info(f"Storage directory created at: {settings.STORAGE_DIR}")
    
    # 初始化数据库
    from database import init_db
    await init_db()
    logger.info("Database initialized")
    
    # ... 现有代码 ...
```

**Step 2:** 确保导入正确

**Step 3:** 提交

```bash
git add backend/main.py
git commit -m "feat: initialize database on startup"
```

---

## 第二阶段：API 增强

### Task 8: 增强 MinerU API - 添加去重和新端点

**Files:**
- Modify: `backend/src/api/mineru.py`
- Modify: `backend/src/models/schemas.py`

**Step 1:** 修改 schemas.py 添加新的响应模型

```python
from pydantic import BaseModel
from typing import Optional, List, Any


class ParseRequest(BaseModel):
    filename: str
    file_content: Optional[bytes] = None
    file_path: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    batch_id: str
    file_name: str
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    state: str
    error_msg: Optional[str] = None
    markdown_content: Optional[str] = None
    result_file_path: Optional[str] = None
    result_file_format: Optional[str] = None
    created_at: str
    updated_at: str
    is_duplicate: Optional[bool] = False  # 标记是否为重复解析


class ParseResult(BaseModel):
    markdown_content: str
    files: List[str]


class ErrorResponse(BaseModel):
    detail: str


class DuplicateCheckRequest(BaseModel):
    file_hash: Optional[str] = None
    file_path: Optional[str] = None


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_task: Optional[TaskResponse] = None


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total: int
    pending: int
    running: int
    done: int
    failed: int
```

**Step 2:** 修改 mineru.py - 添加去重检查和新端点

```python
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from mineru.task_manager import task_manager
from mineru.client import mineru_client
from models.schemas import (
    TaskResponse, ErrorResponse, DuplicateCheckRequest,
    DuplicateCheckResponse, TaskListResponse, StatsResponse
)
from utils.zip_handler import extract_markdown_from_zip
from database import get_db
from utils.file_hash import compute_bytes_hash

router = APIRouter(prefix="/api/mineru", tags=["MinerU"])


class LocalFileParseRequest(BaseModel):
    file_path: str


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(request: DuplicateCheckRequest):
    """检查文件是否已解析"""
    try:
        if request.file_hash:
            file_hash = request.file_hash
        elif request.file_path:
            from utils.file_hash import compute_file_hash
            file_hash = await compute_file_hash(request.file_path)
        else:
            raise HTTPException(status_code=400, detail="必须提供 file_hash 或 file_path")
        
        existing_task = await task_manager.check_duplicate(file_hash)
        return DuplicateCheckResponse(
            is_duplicate=existing_task is not None,
            existing_task=TaskResponse(**existing_task) if existing_task else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"去重检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse", response_model=TaskResponse)
async def parse_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        file_content = await file.read()
        file_hash = compute_bytes_hash(file_content)
        
        # 检查是否已解析
        existing = await task_manager.check_duplicate(file_hash)
        if existing:
            return TaskResponse(**existing, is_duplicate=True)
        
        files = [{"name": file.filename}]
        apply_result = await mineru_client.batch_apply_upload_urls(files)
        batch_id = apply_result["batch_id"]
        upload_url = apply_result["file_urls"][0]
        
        await mineru_client.upload_file(upload_url, file_content)
        
        task = await task_manager.create_task(
            batch_id=batch_id,
            file_name=file.filename or "unknown",
            file_content=file_content,
            file_hash=file_hash
        )
        
        background_tasks.add_task(task_manager.poll_task_status, task["id"])
        
        return TaskResponse(**task)
        
    except Exception as e:
        logger.error(f"解析文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-local", response_model=TaskResponse)
async def parse_local_document(
    background_tasks: BackgroundTasks,
    request: LocalFileParseRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 先检查去重
        from utils.file_hash import compute_file_hash
        file_hash = await compute_file_hash(file_path)
        existing = await task_manager.check_duplicate(file_hash)
        if existing:
            return TaskResponse(**existing, is_duplicate=True)
        
        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()
        
        files = [{"name": file_path.name}]
        apply_result = await mineru_client.batch_apply_upload_urls(files)
        batch_id = apply_result["batch_id"]
        upload_url = apply_result["file_urls"][0]
        
        await mineru_client.upload_file(upload_url, file_content)
        
        task = await task_manager.create_task(
            batch_id=batch_id,
            file_name=file_path.name or "unknown",
            file_path=str(file_path),
            file_content=file_content,
            file_hash=file_hash
        )
        
        background_tasks.add_task(task_manager.poll_task_status, task["id"])
        
        return TaskResponse(**task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析本地文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse(**task)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(limit: int = 100, offset: int = 0):
    """分页获取任务列表"""
    tasks = await task_manager.list_tasks(limit, offset)
    # TODO: 获取总数
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),  # 临时，需要从 repo 获取真实总数
        limit=limit,
        offset=offset
    )


@router.get("/stats", response_model=StatsResponse)
async def get_parse_stats():
    """获取解析统计"""
    stats = await task_manager.get_stats()
    return StatsResponse(**stats)


@router.get("/tasks/{task_id}/result")
async def get_parse_result(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["state"] != "done":
        raise HTTPException(status_code=400, detail="任务未完成")

    # 检查是否已有 markdown_content
    if task.get("markdown_content"):
        return {"markdown_content": task["markdown_content"]}

    try:
        # 获取任务详情（包含 result）
        # TODO: 需要从数据库或其他地方获取完整的 result
        # 临时方案：重新从 MinerU 获取
        task_detail = await task_manager.get_task(task_id)
        # 这里需要补充获取 result 的逻辑
        
        # 现有逻辑
        zip_url = task["result"]["full_zip_url"]  # 注意：这里可能需要调整
        zip_content = await mineru_client.download_zip(zip_url)

        markdown_content = extract_markdown_from_zip(zip_content)

        storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(zip_content)

        # 更新数据库，保存 markdown_content 和 result_file_path
        await task_manager.update_task(
            task_id,
            markdown_content=markdown_content,
            result_file_path=storage_path,
            result_file_format="zip"
        )

        return {"markdown_content": markdown_content}
    except Exception as e:
        logger.error(f"获取解析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/download")
async def download_zip(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["state"] != "done":
        raise HTTPException(status_code=400, detail="任务未完成")

    storage_path = task.get("result_file_path")
    if not storage_path or not os.path.exists(storage_path):
        # 向后兼容：检查旧路径
        storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")
    
    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    with open(storage_path, "rb") as f:
        file_content = f.read()

    file_format = task.get("result_file_format", "zip")
    media_type = "application/zip" if file_format == "zip" else "application/octet-stream"

    return Response(
        content=file_content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={task['file_name']}.{file_format}"
        },
    )
```

**Step 3:** 提交

```bash
git add backend/src/models/schemas.py backend/src/api/mineru.py
git commit -m "feat: enhance MinerU API with deduplication and new endpoints"
```

---

## 第三阶段：前端重构

### Task 9: 创建后端 API 客户端

**Files:**
- Create: `app/src/api/parseBackend.js`
- Modify: `app/src/utils/backend.js`

**Step 1:** 创建 parseBackend.js 封装解析相关 API

```javascript
import { backend } from '@/utils/backend'

export class ParseBackendApi {
  static async checkDuplicate(params) {
    const request = backend.client.post('/api/mineru/check-duplicate', params)
    return await request.json()
  }

  static async parseFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    const request = backend.client.post('/api/mineru/parse', formData)
    return await request.json()
  }

  static async parseLocalFile(filePath) {
    const request = backend.client.post('/api/mineru/parse-local', {
      file_path: filePath
    })
    return await request.json()
  }

  static async getTask(taskId) {
    const request = backend.client.get(`/api/mineru/tasks/${taskId}`)
    return await request.json()
  }

  static async listTasks(limit = 100, offset = 0) {
    const request = backend.client.get(`/api/mineru/tasks?limit=${limit}&offset=${offset}`)
    return await request.json()
  }

  static async getStats() {
    const request = backend.client.get('/api/mineru/stats')
    return await request.json()
  }

  static async getTaskResult(taskId) {
    const request = backend.client.get(`/api/mineru/tasks/${taskId}/result`)
    return await request.json()
  }

  static async downloadResult(taskId) {
    return backend.client.get(`/api/mineru/tasks/${taskId}/download`)
  }
}
```

**Step 2:** 确保 backend.js 正确导出

**Step 3:** 提交

```bash
git add app/src/api/parseBackend.js
git commit -m "feat: add parseBackend API client"
```

---

### Task 10: 重构前端 Parse Store - 移除本地存储

**Files:**
- Modify: `app/src/stores/parse.js`
- Delete: `app/src/repositories/ParseIndexRepository.js`
- Delete: `app/src/repositories/IndexedDBRepository.js`

**Step 1:** 重写 parse.js 使用后端 API

```javascript
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ParseBackendApi } from '@/api/parseBackend'

export const useParseStore = defineStore('parse', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const stats = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchTasks(limit = 100, offset = 0) {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.listTasks(limit, offset)
      tasks.value = response.tasks
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTask(taskId) {
    isLoading.value = true
    error.value = null
    try {
      const task = await ParseBackendApi.getTask(taskId)
      currentTask.value = task
      return task
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await ParseBackendApi.getStats()
      return stats.value
    } catch (err) {
      console.error('获取统计信息失败:', err)
    }
  }

  async function checkDuplicate(params) {
    try {
      return await ParseBackendApi.checkDuplicate(params)
    } catch (err) {
      console.error('去重检查失败:', err)
      return { is_duplicate: false }
    }
  }

  async function parseLocalFile(filePath) {
    isLoading.value = true
    error.value = null
    try {
      const task = await ParseBackendApi.parseLocalFile(filePath)
      if (!task.is_duplicate) {
        await fetchTasks()
      }
      return task
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getTaskResult(taskId) {
    try {
      return await ParseBackendApi.getTaskResult(taskId)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    tasks,
    currentTask,
    stats,
    isLoading,
    error,
    fetchTasks,
    fetchTask,
    fetchStats,
    checkDuplicate,
    parseLocalFile,
    getTaskResult,
    clearError,
  }
})
```

**Step 2:** 删除旧的 repository 文件

```bash
git rm app/src/repositories/ParseIndexRepository.js
git rm app/src/repositories/IndexedDBRepository.js
```

**Step 3:** 提交

```bash
git add app/src/stores/parse.js
git rm app/src/repositories/ParseIndexRepository.js
git rm app/src/repositories/IndexedDBRepository.js
git commit -m "refactor: rewrite parse store to use backend API, remove local storage"
```

---

### Task 11: 更新解析管理页面使用新 Store

**Files:**
- Modify: `app/src/views/ParseManagement.vue`
- Modify: `app/src/components/parse/ParseQueueView.vue`
- Modify: `app/src/components/parse/ParseDocumentsView.vue`
- Modify: `app/src/components/parse/ParseStatsView.vue`

**Step 1:** 更新 ParseManagement.vue 使用新的 parse store

```vue
<script setup>
import { onMounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import ParseQueueView from '@/components/parse/ParseQueueView.vue'
import ParseDocumentsView from '@/components/parse/ParseDocumentsView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'

const parseStore = useParseStore()

onMounted(async () => {
  await parseStore.fetchTasks()
  await parseStore.fetchStats()
})
</script>

<template>
  <div class="parse-management">
    <ParseStatsView />
    <ParseQueueView />
    <ParseDocumentsView />
  </div>
</template>

<style scoped>
.parse-management {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}
</style>
```

**Step 2:** 更新各个子组件使用 parse store

**Step 3:** 提交

```bash
git add app/src/views/ParseManagement.vue
git add app/src/components/parse/ParseQueueView.vue
git add app/src/components/parse/ParseDocumentsView.vue
git add app/src/components/parse/ParseStatsView.vue
git commit -m "refactor: update parse management components to use new store"
```

---

### Task 12: 更新 TextExtractor 使用后端 API

**Files:**
- Modify: `app/src/processors/parse/TextExtractor.js`

**Step 1:** 重写 TextExtractor 使用后端 API

```javascript
import { useParseStore } from '@/stores/parse'

export class TextExtractor {
  static async extract(filePath) {
    const parseStore = useParseStore()
    
    try {
      // 先检查是否已解析
      const duplicateCheck = await parseStore.checkDuplicate({ file_path: filePath })
      
      if (duplicateCheck.is_duplicate && duplicateCheck.existing_task) {
        // 已有解析结果，获取 Markdown 内容
        if (duplicateCheck.existing_task.markdown_content) {
          return {
            success: true,
            markdown: duplicateCheck.existing_task.markdown_content,
            taskId: duplicateCheck.existing_task.id,
            isCached: true
          }
        } else {
          // 需要获取结果
          const result = await parseStore.getTaskResult(duplicateCheck.existing_task.id)
          return {
            success: true,
            markdown: result.markdown_content,
            taskId: duplicateCheck.existing_task.id,
            isCached: true
          }
        }
      }
      
      // 发起新的解析任务
      const task = await parseStore.parseLocalFile(filePath)
      
      return {
        success: true,
        taskId: task.id,
        isDuplicate: task.is_duplicate,
        state: task.state,
        markdown: task.markdown_content
      }
    } catch (error) {
      console.error('文本提取失败:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  static async pollTask(taskId) {
    const parseStore = useParseStore()
    const POLL_INTERVAL = 3000
    const MAX_POLL_ATTEMPTS = 600
    
    for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
      const task = await parseStore.fetchTask(taskId)
      
      if (task.state === 'done') {
        const result = await parseStore.getTaskResult(taskId)
        return {
          success: true,
          markdown: result.markdown_content
        }
      } else if (task.state === 'failed') {
        return {
          success: false,
          error: task.error_msg || '解析失败'
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL))
    }
    
    return {
      success: false,
      error: '解析超时'
    }
  }
}
```

**Step 2:** 提交

```bash
git add app/src/processors/parse/TextExtractor.js
git commit -m "refactor: update TextExtractor to use backend API"
```

---

## 第四阶段：测试与验证

### Task 13: 安装后端依赖并测试

**Step 1:** 安装新依赖

```bash
cd backend
uv sync
```

**Step 2:** 启动后端测试

```bash
python main.py
```

**Step 3:** 验证数据库创建成功

**Step 4:** 测试 API 端点

---

### Task 14: 前端构建和测试

**Step 1:** 运行前端 lint

```bash
cd app
npm run lint
```

**Step 2:** 运行前端 build

```bash
npm run build
```

**Step 3:** 启动前端开发服务器测试

---

### Task 15: 更新文档

**Files:**
- Update: `docs/features/parse-management.md`

**Step 1:** 更新解析管理功能文档

**Step 2:** 提交

```bash
git add docs/features/parse-management.md
git commit -m "docs: update parse management documentation"
```

---

## 总结

### 文件变更总览

**后端新增：**
- `backend/src/database.py` - 数据库连接管理
- `backend/src/models/db_models.py` - 数据库模型
- `backend/src/repositories/parse_task_repository.py` - 数据访问层
- `backend/src/utils/file_hash.py` - 文件哈希工具

**后端修改：**
- `backend/pyproject.toml` - 添加依赖
- `backend/src/config.py` - 添加数据库配置
- `backend/src/mineru/task_manager.py` - 重构使用 SQLite
- `backend/src/models/schemas.py` - 新增响应模型
- `backend/src/api/mineru.py` - 增强 API
- `backend/main.py` - 初始化数据库

**前端新增：**
- `app/src/api/parseBackend.js` - 后端 API 客户端

**前端修改：**
- `app/src/stores/parse.js` - 重构使用后端 API
- `app/src/views/ParseManagement.vue` - 更新页面
- `app/src/components/parse/*.vue` - 更新组件
- `app/src/processors/parse/TextExtractor.js` - 更新提取器

**前端删除：**
- `app/src/repositories/ParseIndexRepository.js`
- `app/src/repositories/IndexedDBRepository.js`

---

**Plan complete and saved to `docs/plans/2026-03-03-sqlite-parse-storage.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
