# QBase v1.2 架构准备阶段实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为新文件管理架构做准备，包括清理未使用依赖、创建目录规范、扩展数据库 Schema。

**Architecture:** 采用渐进式策略，从低风险任务开始，确保与现有系统完全兼容。

**Tech Stack:** Vue 3, Electron, FastAPI, SQLAlchemy, SQLite

---

## 任务 1: 清理 Dexie.js 依赖

**Files:**
- Modify: `app/package.json`
- Delete: `app/package-lock.json` (重新生成)

**Step 1: 从 package.json 移除 dexie**

编辑 `app/package.json`，删除第 22 行的 `"dexie": "^4.3.0",`

**Step 2: 删除 package-lock.json**

```bash
cd app
Remove-Item package-lock.json
```

**Step 3: 重新安装依赖**

```bash
npm install
```

**Step 4: 验证项目仍能正常运行**

```bash
npm run lint
npm run test:unit
```

**Step 5: 提交更改**

```bash
git add app/package.json app/package-lock.json
git commit -m "chore: 移除未使用的 Dexie.js 依赖"
```

---

## 任务 2: 创建 .qbase/ 目录规范

**Files:**
- Create: `backend/src/config/qbase_dir.py`
- Create: `backend/src/services/workspace_service.py`
- Modify: `backend/src/config.py`

**Step 1: 扩展配置文件**

编辑 `backend/src/config.py`，添加以下配置：

```python
# .qbase 目录配置
QBASE_DIR_NAME: str = ".qbase"
GENERATED_DIR_NAME: str = "generated"
INDEXES_DIR_NAME: str = "indexes"
CACHE_DIR_NAME: str = "cache"
CONFIG_FILE_NAME: str = "config.json"
METADATA_DB_NAME: str = "metadata.db"
```

**Step 2: 创建 .qbase 目录管理服务**

创建 `backend/src/services/workspace_service.py`：

```python
import os
import json
from pathlib import Path
from typing import Optional
from loguru import logger


class QBaseWorkspaceService:
    """.qbase 目录管理服务"""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.qbase_dir = self.workspace_root / ".qbase"
        self.generated_dir = self.qbase_dir / "generated"
        self.indexes_dir = self.qbase_dir / "indexes"
        self.cache_dir = self.qbase_dir / "cache"
        self.config_path = self.qbase_dir / "config.json"
        self.metadata_db_path = self.qbase_dir / "metadata.db"

    def initialize_workspace(self) -> bool:
        """初始化工作区 .qbase 目录结构"""
        try:
            # 创建 .qbase 目录
            self.qbase_dir.mkdir(exist_ok=True)
            
            # 创建子目录
            self.generated_dir.mkdir(exist_ok=True)
            self.indexes_dir.mkdir(exist_ok=True)
            self.cache_dir.mkdir(exist_ok=True)
            
            # 创建默认配置文件（如果不存在）
            if not self.config_path.exists():
                self._create_default_config()
            
            # 创建 .gitignore
            self._create_gitignore()
            
            logger.info(f"工作区 {self.workspace_root} 初始化成功")
            return True
        except Exception as e:
            logger.error(f"工作区初始化失败: {e}")
            return False

    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "version": "1.2",
            "workspace": {
                "initialized_at": None
            },
            "ai": {
                "provider": "siliconflow",
                "embedding_model": "BAAI/bge-large-zh-v1.5"
            },
            "sync": {
                "enabled": False,
                "conflict_strategy": "newer_wins"
            }
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

    def _create_gitignore(self):
        """创建 .gitignore 文件"""
        gitignore_content = """# QBase cache
cache/
*.tmp
*.swp
"""
        gitignore_path = self.qbase_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)

    def get_generated_dir_for_hash(self, file_hash: str) -> Path:
        """获取指定哈希的派生数据目录"""
        dir_path = self.generated_dir / file_hash[:16]
        dir_path.mkdir(exist_ok=True)
        return dir_path

    def load_config(self) -> dict:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_config(self, config: dict):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def is_initialized(self) -> bool:
        """检查工作区是否已初始化"""
        return self.qbase_dir.exists()
```

**Step 3: 添加工作区初始化 API**

创建 `backend/src/api/workspace.py`：

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.workspace_service import QBaseWorkspaceService

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class InitializeWorkspaceRequest(BaseModel):
    workspace_path: str


@router.post("/initialize")
async def initialize_workspace(request: InitializeWorkspaceRequest):
    """初始化工作区 .qbase 目录"""
    try:
        service = QBaseWorkspaceService(request.workspace_path)
        success = service.initialize_workspace()
        if success:
            return {"success": True, "message": "工作区初始化成功"}
        else:
            raise HTTPException(status_code=500, detail="工作区初始化失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-initialized")
async def check_initialized(workspace_path: str):
    """检查工作区是否已初始化"""
    service = QBaseWorkspaceService(workspace_path)
    return {"initialized": service.is_initialized()}
```

**Step 4: 在主路由中注册**

修改 `backend/src/main.py`，添加：

```python
from src.api import workspace

app.include_router(workspace.router)
```

**Step 5: 提交更改**

```bash
git add backend/src/config.py
git add backend/src/services/workspace_service.py
git add backend/src/api/workspace.py
git add backend/src/main.py
git commit -m "feat: 添加 .qbase 目录规范和工作区初始化服务"
```

---

## 任务 3: 扩展 SQLite Schema

**Files:**
- Modify: `backend/src/models/db_models.py`
- Create: `backend/src/repositories/file_repository.py`
- Create: `backend/src/repositories/derivative_repository.py`

**Step 1: 添加新的数据库模型**

编辑 `backend/src/models/db_models.py`，在文件末尾添加：

```python
# ============================================
# 新架构表 (v1.2+)
# ============================================

class DBFile(Base):
    """文件索引表 - 基于内容哈希的文件追踪"""
    __tablename__ = "files"

    hash = Column(String(16), primary_key=True, index=True, comment="SHA-256 前16位")
    rel_path = Column(String, unique=True, nullable=False, index=True, comment="相对工作区路径")
    file_type = Column(String(32), nullable=True, comment="文件类型: md | pdf | audio | video")
    size = Column(Integer, nullable=True, comment="文件大小(字节)")
    mtime = Column(Integer, nullable=True, comment="最后修改时间戳")
    status = Column(String(32), nullable=False, default="pending", index=True, comment="状态: pending | processing | ready | error | missing | orphan")
    created_at = Column(Integer, nullable=True, comment="创建时间戳")
    updated_at = Column(Integer, nullable=True, comment="更新时间戳")


class DBDerivative(Base):
    """派生数据表 - AI 生成内容的元数据"""
    __tablename__ = "derivatives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(16), ForeignKey("files.hash", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(32), nullable=False, index=True, comment="类型: raw_text | transcript | notes | flashcards | mindmap | analysis")
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    model_used = Column(String(255), nullable=True, comment="使用的模型")
    status = Column(String(32), nullable=False, default="ready", index=True, comment="状态: ready | outdated | error")
    created_at = Column(Integer, nullable=True, comment="创建时间戳")


class DBTask(Base):
    """任务队列表"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(16), ForeignKey("files.hash"), nullable=True, index=True)
    task_type = Column(String(32), nullable=False, index=True, comment="任务类型: parse | embed | generate | sync")
    status = Column(String(32), nullable=False, index=True, comment="状态: queued | running | success | failed")
    progress = Column(Integer, nullable=False, default=0, comment="进度 0-100")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(Integer, nullable=True, comment="创建时间戳")
    started_at = Column(Integer, nullable=True, comment="开始时间戳")
    completed_at = Column(Integer, nullable=True, comment="完成时间戳")
```

**Step 2: 创建 File Repository**

创建 `backend/src/repositories/file_repository.py`：

```python
from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import DBFile
from loguru import logger


class FileRepository:
    """文件数据访问层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, file_data: dict) -> DBFile:
        """创建文件记录"""
        db_file = DBFile(**file_data)
        self.session.add(db_file)
        await self.session.commit()
        await self.session.refresh(db_file)
        logger.debug(f"创建文件记录: {db_file.hash}")
        return db_file

    async def get_by_hash(self, file_hash: str) -> Optional[DBFile]:
        """通过哈希获取文件"""
        result = await self.session.execute(select(DBFile).where(DBFile.hash == file_hash))
        return result.scalar_one_or_none()

    async def get_by_path(self, rel_path: str) -> Optional[DBFile]:
        """通过相对路径获取文件"""
        result = await self.session.execute(select(DBFile).where(DBFile.rel_path == rel_path))
        return result.scalar_one_or_none()

    async def update(self, file_hash: str, update_data: dict) -> Optional[DBFile]:
        """更新文件记录"""
        stmt = update(DBFile).where(DBFile.hash == file_hash).values(**update_data)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_hash(file_hash)

    async def list_all(self, status: Optional[str] = None) -> List[DBFile]:
        """列出所有文件"""
        query = select(DBFile)
        if status:
            query = query.where(DBFile.status == status)
        result = await self.session.execute(query.order_by(DBFile.updated_at.desc()))
        return list(result.scalars().all())

    async def delete(self, file_hash: str) -> bool:
        """删除文件记录"""
        stmt = delete(DBFile).where(DBFile.hash == file_hash)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
```

**Step 3: 创建 Derivative Repository**

创建 `backend/src/repositories/derivative_repository.py`：

```python
from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import DBDerivative
from loguru import logger


class DerivativeRepository:
    """派生数据访问层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, derivative_data: dict) -> DBDerivative:
        """创建派生数据记录"""
        db_derivative = DBDerivative(**derivative_data)
        self.session.add(db_derivative)
        await self.session.commit()
        await self.session.refresh(db_derivative)
        logger.debug(f"创建派生数据: {db_derivative.file_hash} - {db_derivative.type}")
        return db_derivative

    async def get_by_file_and_type(self, file_hash: str, derivative_type: str) -> Optional[DBDerivative]:
        """获取指定文件的指定类型派生数据"""
        result = await self.session.execute(
            select(DBDerivative)
            .where(DBDerivative.file_hash == file_hash)
            .where(DBDerivative.type == derivative_type)
            .order_by(DBDerivative.version.desc())
        )
        return result.scalar_one_or_none()

    async def list_by_file(self, file_hash: str) -> List[DBDerivative]:
        """列出文件的所有派生数据"""
        result = await self.session.execute(
            select(DBDerivative).where(DBDerivative.file_hash == file_hash)
        )
        return list(result.scalars().all())

    async def update_status(self, derivative_id: int, status: str) -> Optional[DBDerivative]:
        """更新状态"""
        stmt = update(DBDerivative).where(DBDerivative.id == derivative_id).values(status=status)
        await self.session.execute(stmt)
        await self.session.commit()
        result = await self.session.execute(select(DBDerivative).where(DBDerivative.id == derivative_id))
        return result.scalar_one_or_none()
```

**Step 4: 提交更改**

```bash
git add backend/src/models/db_models.py
git add backend/src/repositories/file_repository.py
git add backend/src/repositories/derivative_repository.py
git commit -m "feat: 扩展 SQLite Schema 添加新架构表"
```

---

## 任务 4: 文件哈希计算工具

**Files:**
- Create: `backend/src/utils/file_hash.py`
- Create: `backend/src/api/files.py`

**Step 1: 创建文件哈希工具**

创建 `backend/src/utils/file_hash.py`：

```python
import hashlib
from pathlib import Path
from loguru import logger


def compute_file_hash(file_path: str, length: int = 16) -> str:
    """
    计算文件的 SHA-256 哈希
    
    Args:
        file_path: 文件路径
        length: 返回的哈希长度（默认前16位）
    
    Returns:
        哈希字符串
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # 分块读取大文件
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        full_hash = sha256_hash.hexdigest()
        return full_hash[:length]
    except Exception as e:
        logger.error(f"计算文件哈希失败 {file_path}: {e}")
        raise


def compute_short_hash(content: bytes, length: int = 16) -> str:
    """
    计算内容的短哈希
    
    Args:
        content: 字节内容
        length: 返回的哈希长度
    
    Returns:
        哈希字符串
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()[:length]
```

**Step 2: 创建文件 API**

创建 `backend/src/api/files.py`：

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from src.utils.file_hash import compute_file_hash

router = APIRouter(prefix="/api/files", tags=["files"])


class ComputeHashRequest(BaseModel):
    file_path: str


@router.post("/hash")
async def compute_hash(request: ComputeHashRequest):
    """计算文件哈希"""
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        hash_value = compute_file_hash(str(file_path))
        return {
            "success": True,
            "hash": hash_value,
            "file_path": request.file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3: 在主路由中注册**

修改 `backend/src/main.py`，添加：

```python
from src.api import files

app.include_router(files.router)
```

**Step 4: 提交更改**

```bash
git add backend/src/utils/file_hash.py
git add backend/src/api/files.py
git add backend/src/main.py
git commit -m "feat: 添加文件哈希计算工具和 API"
```

---

## 验证与测试

**运行后端测试：**

```bash
cd backend
python -m pytest
```

**运行前端测试：**

```bash
cd app
npm run test:unit
npm run lint
```

---

## 总结

本计划完成了架构准备阶段的所有任务：

✅ **清理 Dexie.js** - 移除未使用的依赖
✅ **.qbase 目录规范** - 创建标准目录结构和管理服务
✅ **SQLite Schema 扩展** - 添加新架构所需的数据库表
✅ **文件哈希工具** - 实现 SHA-256 哈希计算

这些任务为后续 v1.2 的完整架构迁移奠定了坚实基础。
