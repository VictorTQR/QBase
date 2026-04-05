# 核心文件追踪系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现基于内容哈希的文件追踪系统，支持启动时扫描、相对路径管理和增量更新。

**Architecture:** 采用启动时全量扫描策略，使用 mtime+size 快速过滤，按需计算文件哈希，避免实时监听的复杂性。

**Tech Stack:** Python, FastAPI, SQLAlchemy, SQLite, Electron IPC

---

## 任务 1: 扩展 WorkspaceService 添加扫描功能

**Files:**
- Modify: `backend/src/services/workspace_service.py`

**Step 1: 添加文件扫描方法**

编辑 `backend/src/services/workspace_service.py`，在类末尾添加：

```python
    def scan_workspace(self, force_hash: bool = False) -> dict:
        """
        扫描工作区文件
        
        Args:
            force_hash: 是否强制重新计算所有文件哈希
            
        Returns:
            扫描统计信息
        """
        from pathlib import Path
        import time
        from src.utils.file_hash import compute_file_hash
        
        stats = {
            "total_files": 0,
            "new_files": 0,
            "modified_files": 0,
            "skipped_files": 0,
            "errors": []
        }
        
        supported_extensions = [
            '.md', '.pdf',
            '.mp3', '.wav', '.ogg', '.m4a', '.flac',
            '.mp4', '.webm', '.mov', '.mkv'
        ]
        
        logger.info(f"开始扫描工作区: {self.workspace_root}")
        
        try:
            # 递归遍历工作区
            for file_path in self.workspace_root.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    # 跳过 .qbase 目录
                    if ".qbase" in file_path.parts:
                        continue
                        
                    stats["total_files"] += 1
                    
                    try:
                        rel_path = str(file_path.relative_to(self.workspace_root))
                        mtime = int(file_path.stat().st_mtime)
                        size = file_path.stat().st_size
                        file_type = self._get_file_type(file_path)
                        
                        # 处理文件
                        result = self._process_file(
                            file_path, rel_path, mtime, size, file_type, force_hash
                        )
                        
                        if result == "new":
                            stats["new_files"] += 1
                        elif result == "modified":
                            stats["modified_files"] += 1
                        else:
                            stats["skipped_files"] += 1
                            
                    except Exception as e:
                        error_msg = f"处理文件 {file_path} 失败: {e}"
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)
                        
            logger.info(f"扫描完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"扫描工作区失败: {e}")
            stats["errors"].append(str(e))
            return stats

    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型"""
        ext = file_path.suffix.lower()
        if ext == '.md':
            return 'markdown'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
            return 'audio'
        elif ext in ['.mp4', '.webm', '.mov', '.mkv']:
            return 'video'
        return 'unknown'

    def _process_file(
        self, 
        file_path: Path, 
        rel_path: str, 
        mtime: int, 
        size: int, 
        file_type: str,
        force_hash: bool
    ) -> str:
        """
        处理单个文件
        
        Returns:
            "new" | "modified" | "skipped"
        """
        import time
        from src.utils.file_hash import compute_file_hash
        from src.database import async_session
        from src.repositories.file_repository import FileRepository
        
        # 注意：这里我们暂时使用同步方式，后续可以优化为异步
        # 为了简化，我们直接在内存中处理，不依赖数据库
        
        # 快速检查：mtime + size 没变则跳过
        # 这里简化处理，实际应该查询数据库
        # 暂时直接计算哈希（仅用于演示）
        
        if force_hash:
            file_hash = compute_file_hash(str(file_path))
            logger.debug(f"强制计算哈希: {rel_path} -> {file_hash}")
            return "modified"
        else:
            # 假设未修改（实际应该查询数据库）
            return "skipped"
```

**Step 2: 提交更改**

```bash
git add backend/src/services/workspace_service.py
git commit -m "feat: 添加工作区扫描功能到 WorkspaceService"
```

---

## 任务 2: 创建文件扫描服务

**Files:**
- Create: `backend/src/services/file_scanner.py`

**Step 1: 创建文件扫描服务**

创建 `backend/src/services/file_scanner.py`：

```python
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import DBFile
from src.utils.file_hash import compute_file_hash


class FileScanner:
    """文件扫描服务 - 启动时扫描工作区"""

    SUPPORTED_EXTENSIONS = [
        '.md', '.pdf',
        '.mp3', '.wav', '.ogg', '.m4a', '.flac',
        '.mp4', '.webm', '.mov', '.mkv'
    ]

    def __init__(self, workspace_root: str, session: AsyncSession):
        self.workspace_root = Path(workspace_root)
        self.session = session

    async def scan_full(self, force_hash: bool = False) -> Dict:
        """
        全量扫描工作区
        
        Args:
            force_hash: 是否强制重新计算所有文件哈希
            
        Returns:
            扫描统计信息
        """
        stats = {
            "total_files": 0,
            "new_files": 0,
            "modified_files": 0,
            "unchanged_files": 0,
            "deleted_files": 0,
            "errors": []
        }

        logger.info(f"开始全量扫描: {self.workspace_root}")
        start_time = time.time()

        try:
            # 1. 获取数据库中已有的文件
            existing_files = await self._get_existing_files()
            logger.debug(f"数据库中现有文件数: {len(existing_files)}")

            # 2. 扫描文件系统
            current_files = {}
            for file_path in self.workspace_root.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    # 跳过 .qbase 目录
                    if ".qbase" in file_path.parts:
                        continue

                    stats["total_files"] += 1
                    rel_path = str(file_path.relative_to(self.workspace_root))
                    current_files[rel_path] = file_path

            # 3. 处理每个文件
            for rel_path, file_path in current_files.items():
                try:
                    result = await self._process_file(
                        file_path, rel_path, existing_files.get(rel_path), force_hash
                    )
                    
                    if result == "new":
                        stats["new_files"] += 1
                    elif result == "modified":
                        stats["modified_files"] += 1
                    else:
                        stats["unchanged_files"] += 1
                        
                except Exception as e:
                    error_msg = f"处理文件 {rel_path} 失败: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

            # 4. 标记已删除的文件
            for rel_path, db_file in existing_files.items():
                if rel_path not in current_files:
                    await self._mark_file_missing(db_file)
                    stats["deleted_files"] += 1

            elapsed = time.time() - start_time
            logger.info(f"扫描完成，耗时 {elapsed:.2f}s: {stats}")
            return stats

        except Exception as e:
            logger.error(f"扫描失败: {e}")
            stats["errors"].append(str(e))
            return stats

    async def _get_existing_files(self) -> Dict[str, DBFile]:
        """获取数据库中已有的文件"""
        result = await self.session.execute(select(DBFile))
        files = result.scalars().all()
        return {f.rel_path: f for f in files}

    async def _process_file(
        self,
        file_path: Path,
        rel_path: str,
        existing_file: Optional[DBFile],
        force_hash: bool
    ) -> str:
        """
        处理单个文件
        
        Returns:
            "new" | "modified" | "unchanged"
        """
        import time
        
        stats = file_path.stat()
        mtime = int(stats.st_mtime)
        size = stats.st_size
        file_type = self._get_file_type(file_path)

        if existing_file:
            # 快速检查：mtime + size 没变则跳过
            if not force_hash and existing_file.mtime == mtime and existing_file.size == size:
                return "unchanged"

            # 需要更新
            file_hash = compute_file_hash(str(file_path))
            
            # 如果哈希没变，只更新 mtime/size
            if existing_file.hash == file_hash:
                existing_file.mtime = mtime
                existing_file.size = size
                existing_file.updated_at = int(time.time())
                await self.session.commit()
                return "unchanged"

            # 哈希变了，完整更新
            existing_file.hash = file_hash
            existing_file.mtime = mtime
            existing_file.size = size
            existing_file.file_type = file_type
            existing_file.status = "pending"
            existing_file.updated_at = int(time.time())
            await self.session.commit()
            return "modified"

        else:
            # 新文件
            file_hash = compute_file_hash(str(file_path))
            now = int(time.time())
            
            db_file = DBFile(
                hash=file_hash,
                rel_path=rel_path,
                file_type=file_type,
                size=size,
                mtime=mtime,
                status="pending",
                created_at=now,
                updated_at=now
            )
            
            self.session.add(db_file)
            await self.session.commit()
            return "new"

    async def _mark_file_missing(self, db_file: DBFile):
        """标记文件为缺失"""
        import time
        db_file.status = "missing"
        db_file.updated_at = int(time.time())
        await self.session.commit()
        logger.debug(f"标记文件为缺失: {db_file.rel_path}")

    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型"""
        ext = file_path.suffix.lower()
        if ext == '.md':
            return 'markdown'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
            return 'audio'
        elif ext in ['.mp4', '.webm', '.mov', '.mkv']:
            return 'video'
        return 'unknown'
```

**Step 2: 提交更改**

```bash
git add backend/src/services/file_scanner.py
git commit -m "feat: 创建 FileScanner 文件扫描服务"
```

---

## 任务 3: 添加扫描 API

**Files:**
- Modify: `backend/src/api/workspace.py`

**Step 1: 扩展工作区 API**

编辑 `backend/src/api/workspace.py`，替换为：

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.services.workspace_service import QBaseWorkspaceService
from src.services.file_scanner import FileScanner

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class InitializeWorkspaceRequest(BaseModel):
    workspace_path: str


class ScanWorkspaceRequest(BaseModel):
    workspace_path: str
    force_hash: bool = False


async def get_session():
    async with async_session() as session:
        yield session


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


@router.post("/scan")
async def scan_workspace(
    request: ScanWorkspaceRequest,
    session: AsyncSession = Depends(get_session)
):
    """扫描工作区文件"""
    try:
        # 先确保工作区已初始化
        workspace_service = QBaseWorkspaceService(request.workspace_path)
        if not workspace_service.is_initialized():
            workspace_service.initialize_workspace()
        
        # 执行扫描
        scanner = FileScanner(request.workspace_path, session)
        stats = await scanner.scan_full(force_hash=request.force_hash)
        
        return {
            "success": True,
            "message": "扫描完成",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 提交更改**

```bash
git add backend/src/api/workspace.py
git commit -m "feat: 添加工作区扫描 API"
```

---

## 任务 4: 添加文件查询 API

**Files:**
- Modify: `backend/src/api/files.py`

**Step 1: 扩展文件 API**

编辑 `backend/src/api/files.py`，替换为：

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.models.db_models import DBFile
from src.repositories.file_repository import FileRepository
from src.utils.file_hash import compute_file_hash

router = APIRouter(prefix="/api/files", tags=["files"])


class ComputeHashRequest(BaseModel):
    file_path: str


async def get_session():
    async with async_session() as session:
        yield session


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


@router.get("/list")
async def list_files(
    workspace_path: str,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """列出工作区文件"""
    try:
        query = select(DBFile)
        if status:
            query = query.where(DBFile.status == status)
        query = query.order_by(desc(DBFile.updated_at)).offset(offset).limit(limit)
        
        result = await session.execute(query)
        files = result.scalars().all()
        
        # 转换为字典
        file_list = []
        for f in files:
            file_list.append({
                "hash": f.hash,
                "rel_path": f.rel_path,
                "file_type": f.file_type,
                "size": f.size,
                "mtime": f.mtime,
                "status": f.status,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
                "absolute_path": str(Path(workspace_path) / f.rel_path) if workspace_path else None
            })
        
        # 获取总数
        count_query = select(DBFile)
        if status:
            count_query = count_query.where(DBFile.status == status)
        count_result = await session.execute(count_query)
        total = len(count_result.scalars().all())
        
        return {
            "success": True,
            "files": file_list,
            "total": total,
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_hash}")
async def get_file(
    file_hash: str,
    workspace_path: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """获取单个文件信息"""
    try:
        repo = FileRepository(session)
        db_file = await repo.get_by_hash(file_hash)
        
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "success": True,
            "file": {
                "hash": db_file.hash,
                "rel_path": db_file.rel_path,
                "file_type": db_file.file_type,
                "size": db_file.size,
                "mtime": db_file.mtime,
                "status": db_file.status,
                "created_at": db_file.created_at,
                "updated_at": db_file.updated_at,
                "absolute_path": str(Path(workspace_path) / db_file.rel_path) if workspace_path else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_hash}")
async def delete_file(
    file_hash: str,
    session: AsyncSession = Depends(get_session)
):
    """删除文件记录（不删除物理文件）"""
    try:
        repo = FileRepository(session)
        success = await repo.delete(file_hash)
        
        if not success:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {"success": True, "message": "文件记录已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 提交更改**

```bash
git add backend/src/api/files.py
git commit -m "feat: 扩展文件 API，添加列表和详情查询"
```

---

## 任务 5: 前端 API 客户端

**Files:**
- Create: `app/src/api/workspaceBackend.js`

**Step 1: 创建工作区后端 API 客户端**

创建 `app/src/api/workspaceBackend.js`：

```javascript
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class WorkspaceBackendApi {
  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || '请求失败')
      }
      return data
    } catch (error) {
      console.error('Workspace API Error:', error)
      throw error
    }
  }

  async initializeWorkspace(workspacePath) {
    return this.request('/api/workspace/initialize', {
      method: 'POST',
      body: JSON.stringify({ workspace_path: workspacePath }),
    })
  }

  async checkInitialized(workspacePath) {
    return this.request(`/api/workspace/check-initialized?workspace_path=${encodeURIComponent(workspacePath)}`)
  }

  async scanWorkspace(workspacePath, forceHash = false) {
    return this.request('/api/workspace/scan', {
      method: 'POST',
      body: JSON.stringify({
        workspace_path: workspacePath,
        force_hash: forceHash,
      }),
    })
  }
}

export const workspaceBackendApi = new WorkspaceBackendApi()
```

**Step 2: 创建文件后端 API 客户端**

创建 `app/src/api/fileBackend.js`：

```javascript
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class FileBackendApi {
  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || '请求失败')
      }
      return data
    } catch (error) {
      console.error('File API Error:', error)
      throw error
    }
  }

  async computeHash(filePath) {
    return this.request('/api/files/hash', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath }),
    })
  }

  async listFiles(workspacePath, options = {}) {
    const { status = null, offset = 0, limit = 100 } = options
    let url = `/api/files/list?workspace_path=${encodeURIComponent(workspacePath)}&offset=${offset}&limit=${limit}`
    if (status) {
      url += `&status=${status}`
    }
    return this.request(url)
  }

  async getFile(fileHash, workspacePath = null) {
    let url = `/api/files/${fileHash}`
    if (workspacePath) {
      url += `?workspace_path=${encodeURIComponent(workspacePath)}`
    }
    return this.request(url)
  }

  async deleteFile(fileHash) {
    return this.request(`/api/files/${fileHash}`, {
      method: 'DELETE',
    })
  }
}

export const fileBackendApi = new FileBackendApi()
```

**Step 3: 提交更改**

```bash
git add app/src/api/workspaceBackend.js
git add app/src/api/fileBackend.js
git commit -m "feat: 添加工作区和文件后端 API 客户端"
```

---

## 任务 6: 前端文件管理 Store

**Files:**
- Create: `app/src/stores/fileManagement.js`

**Step 1: 创建文件管理 Store**

创建 `app/src/stores/fileManagement.js`：

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { workspaceBackendApi } from '@/api/workspaceBackend'
import { fileBackendApi } from '@/api/fileBackend'

export const useFileManagementStore = defineStore('fileManagement', () => {
  const files = ref([])
  const totalFiles = ref(0)
  const isLoading = ref(false)
  const isScanning = ref(false)
  const scanStats = ref(null)
  const selectedFile = ref(null)

  const pendingFiles = computed(() => 
    files.value.filter(f => f.status === 'pending')
  )

  const readyFiles = computed(() => 
    files.value.filter(f => f.status === 'ready')
  )

  const missingFiles = computed(() => 
    files.value.filter(f => f.status === 'missing')
  )

  async function initializeAndScanWorkspace(workspacePath) {
    try {
      isLoading.value = true
      
      // 检查并初始化工作区
      const initCheck = await workspaceBackendApi.checkInitialized(workspacePath)
      if (!initCheck.initialized) {
        await workspaceBackendApi.initializeWorkspace(workspacePath)
        ElMessage.success('工作区初始化成功')
      }

      // 扫描工作区
      await scanWorkspace(workspacePath)
      
    } catch (error) {
      console.error('初始化工作区失败:', error)
      ElMessage.error(`初始化失败: ${error.message}`)
    } finally {
      isLoading.value = false
    }
  }

  async function scanWorkspace(workspacePath, forceHash = false) {
    try {
      isScanning.value = true
      scanStats.value = null
      
      const result = await workspaceBackendApi.scanWorkspace(workspacePath, forceHash)
      scanStats.value = result.stats
      
      ElMessage.success(`扫描完成: 新增 ${result.stats.new_files} 个，修改 ${result.stats.modified_files} 个`)
      
      // 刷新文件列表
      await loadFiles(workspacePath)
      
    } catch (error) {
      console.error('扫描工作区失败:', error)
      ElMessage.error(`扫描失败: ${error.message}`)
    } finally {
      isScanning.value = false
    }
  }

  async function loadFiles(workspacePath, options = {}) {
    try {
      isLoading.value = true
      
      const result = await fileBackendApi.listFiles(workspacePath, options)
      files.value = result.files
      totalFiles.value = result.total
      
    } catch (error) {
      console.error('加载文件列表失败:', error)
      ElMessage.error(`加载失败: ${error.message}`)
    } finally {
      isLoading.value = false
    }
  }

  async function loadFileDetail(fileHash, workspacePath) {
    try {
      const result = await fileBackendApi.getFile(fileHash, workspacePath)
      selectedFile.value = result.file
      return result.file
    } catch (error) {
      console.error('加载文件详情失败:', error)
      ElMessage.error(`加载失败: ${error.message}`)
    }
  }

  function selectFile(file) {
    selectedFile.value = file
  }

  function clearSelection() {
    selectedFile.value = null
  }

  return {
    files,
    totalFiles,
    isLoading,
    isScanning,
    scanStats,
    selectedFile,
    pendingFiles,
    readyFiles,
    missingFiles,
    initializeAndScanWorkspace,
    scanWorkspace,
    loadFiles,
    loadFileDetail,
    selectFile,
    clearSelection,
  }
})
```

**Step 2: 提交更改**

```bash
git add app/src/stores/fileManagement.js
git commit -m "feat: 创建文件管理 Store"
```

---

## 验证与测试

**运行后端：**

```bash
cd backend
python -m uvicorn src.main:app --reload
```

**测试 API：**

```bash
# 初始化工作区
curl -X POST http://localhost:8000/api/workspace/initialize \
  -H "Content-Type: application/json" \
  -d '{"workspace_path": "/path/to/your/workspace"}'

# 扫描工作区
curl -X POST http://localhost:8000/api/workspace/scan \
  -H "Content-Type: application/json" \
  -d '{"workspace_path": "/path/to/your/workspace"}'

# 列出文件
curl "http://localhost:8000/api/files/list?workspace_path=/path/to/your/workspace"
```

**运行前端：**

```bash
cd app
npm run dev
```

---

## 总结

本计划完成了核心文件追踪系统的以下功能：

✅ **FileScanner 服务** - 启动时扫描工作区，使用 mtime+size 快速过滤  
✅ **文件哈希计算** - SHA-256 前16位作为文件标识  
✅ **相对路径管理** - 支持跨设备兼容性  
✅ **完整的 REST API** - 初始化、扫描、列表、详情查询  
✅ **前端 API 客户端** - workspaceBackendApi + fileBackendApi  
✅ **Pinia Store** - useFileManagementStore 状态管理  

为下一阶段的派生数据落盘和双写策略奠定了基础。
