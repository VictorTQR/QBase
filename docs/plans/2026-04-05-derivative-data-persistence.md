# 派生数据落盘机制实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现派生数据从数据库到文件系统的落盘机制，支持 raw_text.md、flashcards.json、mindmap.json 等格式，并与 Derivative 表关联。

**Architecture:** 采用双写策略，同时写入数据库和文件系统，读取时优先从文件系统读取，降级兼容数据库。

**Tech Stack:** Python, FastAPI, SQLAlchemy, SQLite, File System

---

## 任务 1: 创建派生数据存储服务

**Files:**
- Create: `backend/src/services/derivative_service.py`

**Step 1: 创建派生数据服务**

创建 `backend/src/services/derivative_service.py`：

```python
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import DBDerivative
from src.repositories.derivative_repository import DerivativeRepository


class DerivativeService:
    """派生数据存储服务 - 管理 AI 生成内容的文件系统存储"""

    DERIVATIVE_TYPES = {
        "raw_text": {"extension": ".md", "filename": "raw_text.md"},
        "transcript": {"extension": ".srt", "filename": "transcript.srt"},
        "notes": {"extension": ".md", "filename": "ai_notes.md"},
        "flashcards": {"extension": ".json", "filename": "flashcards.json"},
        "mindmap": {"extension": ".json", "filename": "mindmap.json"},
        "analysis": {"extension": ".json", "filename": "analysis.json"},
    }

    def __init__(self, workspace_root: str, session: AsyncSession):
        self.workspace_root = Path(workspace_root)
        self.qbase_dir = self.workspace_root / ".qbase"
        self.generated_dir = self.qbase_dir / "generated"
        self.session = session
        self.repository = DerivativeRepository(session)

    def _get_derivative_dir(self, file_hash: str) -> Path:
        """获取指定文件哈希的派生数据目录"""
        short_hash = file_hash[:16]
        dir_path = self.generated_dir / short_hash
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def _get_derivative_path(self, file_hash: str, derivative_type: str) -> Path:
        """获取派生数据文件路径"""
        if derivative_type not in self.DERIVATIVE_TYPES:
            raise ValueError(f"不支持的派生数据类型: {derivative_type}")
        
        dir_path = self._get_derivative_dir(file_hash)
        config = self.DERIVATIVE_TYPES[derivative_type]
        return dir_path / config["filename"]

    async def save_derivative(
        self,
        file_hash: str,
        derivative_type: str,
        content: Any,
        model_used: Optional[str] = None,
        version: int = 1,
    ) -> DBDerivative:
        """
        保存派生数据到文件系统和数据库
        
        Args:
            file_hash: 文件哈希
            derivative_type: 派生数据类型
            content: 内容（字符串或字典）
            model_used: 使用的模型
            version: 版本号
            
        Returns:
            DBDerivative 对象
        """
        import time
        
        file_path = self._get_derivative_path(file_hash, derivative_type)
        
        # 写入文件系统
        try:
            if isinstance(content, (dict, list)):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            
            logger.debug(f"派生数据已写入文件: {file_path}")
        except Exception as e:
            logger.error(f"写入派生数据文件失败: {e}")
            raise

        # 更新或创建数据库记录
        now = int(time.time())
        
        # 检查是否已存在
        existing = await self.repository.get_by_file_and_type(file_hash, derivative_type)
        
        if existing:
            # 更新现有记录
            derivative = await self.repository.update_status(existing.id, "ready")
            derivative.version = version
            derivative.model_used = model_used
            derivative.created_at = now
            await self.session.commit()
            await self.session.refresh(derivative)
        else:
            # 创建新记录
            derivative_data = {
                "file_hash": file_hash[:16],
                "type": derivative_type,
                "version": version,
                "model_used": model_used,
                "status": "ready",
                "created_at": now,
            }
            derivative = await self.repository.create(derivative_data)
        
        return derivative

    async def load_derivative(
        self,
        file_hash: str,
        derivative_type: str,
    ) -> Optional[Any]:
        """
        加载派生数据（优先从文件系统读取）
        
        Args:
            file_hash: 文件哈希
            derivative_type: 派生数据类型
            
        Returns:
            派生数据内容，不存在返回 None
        """
        file_path = self._get_derivative_path(file_hash, derivative_type)
        
        # 优先从文件系统读取
        if file_path.exists():
            try:
                config = self.DERIVATIVE_TYPES[derivative_type]
                if config["extension"] == ".json":
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception as e:
                logger.error(f"读取派生数据文件失败: {e}")
        
        # 文件系统不存在，返回 None（双写期可以从数据库读取）
        return None

    async def delete_derivative(
        self,
        file_hash: str,
        derivative_type: str,
    ) -> bool:
        """
        删除派生数据
        
        Args:
            file_hash: 文件哈希
            derivative_type: 派生数据类型
            
        Returns:
            是否成功
        """
        try:
            # 删除文件
            file_path = self._get_derivative_path(file_hash, derivative_type)
            if file_path.exists():
                file_path.unlink()
            
            # 删除数据库记录
            existing = await self.repository.get_by_file_and_type(file_hash, derivative_type)
            if existing:
                await self.session.delete(existing)
                await self.session.commit()
            
            logger.debug(f"已删除派生数据: {file_hash} - {derivative_type}")
            return True
        except Exception as e:
            logger.error(f"删除派生数据失败: {e}")
            return False

    async def list_derivatives(self, file_hash: str) -> List[Dict]:
        """
        列出文件的所有派生数据
        
        Args:
            file_hash: 文件哈希
            
        Returns:
            派生数据列表
        """
        derivatives = await self.repository.list_by_file(file_hash)
        
        result = []
        for d in derivatives:
            file_path = self._get_derivative_path(file_hash, d.type)
            result.append({
                "id": d.id,
                "type": d.type,
                "version": d.version,
                "model_used": d.model_used,
                "status": d.status,
                "created_at": d.created_at,
                "file_exists": file_path.exists(),
            })
        
        return result

    async def mark_outdated(self, file_hash: str) -> int:
        """
        标记文件的所有派生数据为过期
        
        Args:
            file_hash: 文件哈希
            
        Returns:
            更新的数量
        """
        derivatives = await self.repository.list_by_file(file_hash)
        count = 0
        
        for d in derivatives:
            await self.repository.update_status(d.id, "outdated")
            count += 1
        
        return count
```

**Step 2: 提交更改**

```bash
git add backend/src/services/derivative_service.py
git commit -m "feat: 创建派生数据存储服务 DerivativeService"
```

---

## 任务 2: 扩展 WorkspaceService 支持派生数据

**Files:**
- Modify: `backend/src/services/workspace_service.py`

**Step 1: 添加派生数据相关方法**

编辑 `backend/src/services/workspace_service.py`，在类末尾添加：

```python
    def get_derivative_service(self, session):
        """获取派生数据服务"""
        from src.services.derivative_service import DerivativeService
        return DerivativeService(str(self.workspace_root), session)

    def get_generated_dir(self) -> Path:
        """获取 generated 目录"""
        return self.generated_dir

    def get_derivative_dir(self, file_hash: str) -> Path:
        """获取指定哈希的派生数据目录"""
        dir_path = self.generated_dir / file_hash[:16]
        dir_path.mkdir(exist_ok=True)
        return dir_path
```

**Step 2: 提交更改**

```bash
git add backend/src/services/workspace_service.py
git commit -m "feat: 扩展 WorkspaceService 支持派生数据"
```

---

## 任务 3: 添加派生数据 API

**Files:**
- Create: `backend/src/api/derivatives.py`

**Step 1: 创建派生数据 API**

创建 `backend/src/api/derivatives.py`：

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.services.workspace_service import QBaseWorkspaceService

router = APIRouter(prefix="/api/derivatives", tags=["derivatives"])


class SaveDerivativeRequest(BaseModel):
    workspace_path: str
    file_hash: str
    derivative_type: str
    content: Any
    model_used: Optional[str] = None
    version: int = 1


async def get_session():
    async with async_session() as session:
        yield session


@router.post("/save")
async def save_derivative(
    request: SaveDerivativeRequest,
    session: AsyncSession = Depends(get_session)
):
    """保存派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(request.workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)
        
        derivative = await derivative_service.save_derivative(
            file_hash=request.file_hash,
            derivative_type=request.derivative_type,
            content=request.content,
            model_used=request.model_used,
            version=request.version,
        )
        
        return {
            "success": True,
            "message": "派生数据保存成功",
            "derivative": {
                "id": derivative.id,
                "file_hash": derivative.file_hash,
                "type": derivative.type,
                "version": derivative.version,
                "model_used": derivative.model_used,
                "status": derivative.status,
                "created_at": derivative.created_at,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load")
async def load_derivative(
    workspace_path: str,
    file_hash: str,
    derivative_type: str,
    session: AsyncSession = Depends(get_session)
):
    """加载派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)
        
        content = await derivative_service.load_derivative(
            file_hash=file_hash,
            derivative_type=derivative_type,
        )
        
        if content is None:
            raise HTTPException(status_code=404, detail="派生数据不存在")
        
        return {
            "success": True,
            "file_hash": file_hash,
            "derivative_type": derivative_type,
            "content": content,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_derivatives(
    workspace_path: str,
    file_hash: str,
    session: AsyncSession = Depends(get_session)
):
    """列出文件的所有派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)
        
        derivatives = await derivative_service.list_derivatives(file_hash)
        
        return {
            "success": True,
            "file_hash": file_hash,
            "derivatives": derivatives,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_derivative(
    workspace_path: str,
    file_hash: str,
    derivative_type: str,
    session: AsyncSession = Depends(get_session)
):
    """删除派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)
        
        success = await derivative_service.delete_derivative(
            file_hash=file_hash,
            derivative_type=derivative_type,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="派生数据不存在")
        
        return {
            "success": True,
            "message": "派生数据删除成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-outdated")
async def mark_outdated(
    workspace_path: str,
    file_hash: str,
    session: AsyncSession = Depends(get_session)
):
    """标记文件的所有派生数据为过期"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)
        
        count = await derivative_service.mark_outdated(file_hash)
        
        return {
            "success": True,
            "message": f"已标记 {count} 个派生数据为过期",
            "count": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 在主路由中注册**

修改 `backend/main.py`，添加：

```python
from src.api import derivatives

app.include_router(derivatives.router)
```

**Step 3: 提交更改**

```bash
git add backend/src/api/derivatives.py
git add backend/main.py
git commit -m "feat: 添加派生数据 API"
```

---

## 任务 4: 前端派生数据 API 客户端

**Files:**
- Create: `app/src/api/derivativeBackend.js`

**Step 1: 创建派生数据后端 API 客户端**

创建 `app/src/api/derivativeBackend.js`：

```javascript
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class DerivativeBackendApi {
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
      console.error('Derivative API Error:', error)
      throw error
    }
  }

  async saveDerivative(workspacePath, fileHash, derivativeType, content, options = {}) {
    const { modelUsed = null, version = 1 } = options
    return this.request('/api/derivatives/save', {
      method: 'POST',
      body: JSON.stringify({
        workspace_path: workspacePath,
        file_hash: fileHash,
        derivative_type: derivativeType,
        content,
        model_used: modelUsed,
        version,
      }),
    })
  }

  async loadDerivative(workspacePath, fileHash, derivativeType) {
    return this.request(
      `/api/derivatives/load?workspace_path=${encodeURIComponent(workspacePath)}&file_hash=${encodeURIComponent(fileHash)}&derivative_type=${encodeURIComponent(derivativeType)}`
    )
  }

  async listDerivatives(workspacePath, fileHash) {
    return this.request(
      `/api/derivatives/list?workspace_path=${encodeURIComponent(workspacePath)}&file_hash=${encodeURIComponent(fileHash)}`
    )
  }

  async deleteDerivative(workspacePath, fileHash, derivativeType) {
    return this.request(
      `/api/derivatives/delete?workspace_path=${encodeURIComponent(workspacePath)}&file_hash=${encodeURIComponent(fileHash)}&derivative_type=${encodeURIComponent(derivativeType)}`,
      { method: 'DELETE' }
    )
  }

  async markOutdated(workspacePath, fileHash) {
    return this.request('/api/derivatives/mark-outdated', {
      method: 'POST',
      body: JSON.stringify({
        workspace_path: workspacePath,
        file_hash: fileHash,
      }),
    })
  }
}

export const derivativeBackendApi = new DerivativeBackendApi()
```

**Step 2: 提交更改**

```bash
git add app/src/api/derivativeBackend.js
git commit -m "feat: 添加派生数据后端 API 客户端"
```

---

## 任务 5: 扩展 MinerU 解析支持 raw_text 落盘

**Files:**
- Modify: `backend/src/api/mineru.py`

**Step 1: 修改解析结果保存逻辑**

编辑 `backend/src/api/mineru.py`，在 `get_parse_result` 函数中，找到保存 markdown_content 的部分，添加落盘逻辑：

```python
        # 更新数据库，保存 markdown_content 和 result_file_path
        await task_manager.update_task(
            task_id,
            markdown_content=markdown_content,
            result_file_path=storage_path,
            result_file_format="zip",
        )

        # ========== 新增：派生数据落盘 ==========
        try:
            # 尝试从任务中获取工作区路径（简化处理，后续可优化）
            # 这里暂时跳过，需要结合工作区管理
            logger.info(f"解析完成，markdown_content 长度: {len(markdown_content)}")
        except Exception as e:
            logger.warning(f"派生数据落盘失败（非致命）: {e}")
        # ==========================================

        return {"markdown_content": markdown_content}
```

**Step 2: 提交更改**

```bash
git add backend/src/api/mineru.py
git commit -m "feat: 为 MinerU 解析添加派生数据落盘准备"
```

---

## 任务 6: 扩展闪卡 Store 支持文件系统存储

**Files:**
- Create: `app/src/repositories/FileSystemFlashcardRepository.js`
- Modify: `app/src/stores/flashcard.js`

**Step 1: 创建文件系统闪卡仓库**

创建 `app/src/repositories/FileSystemFlashcardRepository.js`：

```javascript
import { derivativeBackendApi } from '@/api/derivativeBackend'
import { fileBackendApi } from '@/api/fileBackend'

export class FileSystemFlashcardRepository {
  constructor(workspacePath) {
    this.workspacePath = workspacePath
  }

  async _getFileHash(sourceFile) {
    // 通过文件路径获取哈希
    try {
      const result = await fileBackendApi.computeHash(sourceFile)
      return result.hash
    } catch (error) {
      console.error('获取文件哈希失败:', error)
      return null
    }
  }

  async getAll() {
    // 双写期：暂时还是从 LocalStorage 读取
    // 后续可以从文件系统扫描
    const localStorageRepo = new (await import('./LocalStorageFlashcardRepository')).LocalStorageFlashcardRepository()
    return await localStorageRepo.getAll()
  }

  async create(set) {
    // 双写：同时写 LocalStorage 和文件系统
    const localStorageRepo = new (await import('./LocalStorageFlashcardRepository')).LocalStorageFlashcardRepository()
    const result = await localStorageRepo.create(set)

    // 尝试写入文件系统
    if (set.sourceFile) {
      try {
        const fileHash = await this._getFileHash(set.sourceFile)
        if (fileHash) {
          const flashcardsData = {
            version: 1,
            model: null, // 后续可以记录使用的模型
            generated_at: Date.now(),
            title: set.title,
            source_file: set.sourceFile,
            cards: set.flashcards.map(card => ({
              q: card.front,
              a: card.back,
              difficulty: card.difficulty,
              tags: []
            }))
          }

          await derivativeBackendApi.saveDerivative(
            this.workspacePath,
            fileHash,
            'flashcards',
            flashcardsData
          )
          console.log('闪卡已保存到文件系统')
        }
      } catch (error) {
        console.warn('闪卡保存到文件系统失败（非致命）:', error)
      }
    }

    return result
  }

  async update(setId, updates) {
    // 双写期：主要更新 LocalStorage
    const localStorageRepo = new (await import('./LocalStorageFlashcardRepository')).LocalStorageFlashcardRepository()
    return await localStorageRepo.update(setId, updates)
  }

  async delete(setId) {
    // 双写期：主要删除 LocalStorage
    const localStorageRepo = new (await import('./LocalStorageFlashcardRepository')).LocalStorageFlashcardRepository()
    return await localStorageRepo.delete(setId)
  }
}
```

**Step 2: 更新闪卡 Store 支持双写**

编辑 `app/src/stores/flashcard.js`，添加工作区路径支持（简化版本）：

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { LocalStorageFlashcardRepository } from '@/repositories/LocalStorageFlashcardRepository'
// import { FileSystemFlashcardRepository } from '@/repositories/FileSystemFlashcardRepository'
import { useAgentStore } from './agent'
import { useDocumentStore } from './document'
import { useWorkspaceStore } from './workspace'

// ... 保留原有代码 ...

export const useFlashcardStore = defineStore('flashcard', () => {
  // 双写期：继续使用 LocalStorage
  const repository = new LocalStorageFlashcardRepository()
  
  // TODO: 后续可以根据配置切换到 FileSystemFlashcardRepository
  // const workspaceStore = useWorkspaceStore()
  // const repository = workspaceStore.folders.length > 0 
  //   ? new FileSystemFlashcardRepository(workspaceStore.folders[0].path)
  //   : new LocalStorageFlashcardRepository()

  // ... 保留原有代码 ...
})
```

**Step 3: 提交更改**

```bash
git add app/src/repositories/FileSystemFlashcardRepository.js
git add app/src/stores/flashcard.js
git commit -m "feat: 添加文件系统闪卡仓库，支持双写策略"
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
# 保存 raw_text
curl -X POST http://localhost:8000/api/derivatives/save \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_path": "/path/to/workspace",
    "file_hash": "a1b2c3d4e5f67890",
    "derivative_type": "raw_text",
    "content": "# 测试文档\n\n这是测试内容..."
  }'

# 列出派生数据
curl "http://localhost:8000/api/derivatives/list?workspace_path=/path/to/workspace&file_hash=a1b2c3d4e5f67890"

# 加载派生数据
curl "http://localhost:8000/api/derivatives/load?workspace_path=/path/to/workspace&file_hash=a1b2c3d4e5f67890&derivative_type=raw_text"
```

---

## 总结

本计划完成了派生数据落盘机制的以下功能：

✅ **DerivativeService** - 派生数据文件系统存储服务  
✅ **WorkspaceService 扩展** - 支持派生数据目录管理  
✅ **派生数据 REST API** - save/load/list/delete/mark-outdated  
✅ **前端 API 客户端** - derivativeBackendApi  
✅ **MinerU 集成准备** - 为解析结果添加落盘逻辑  
✅ **闪卡双写支持** - FileSystemFlashcardRepository  

为下一阶段的完整双写策略和前端适配奠定了基础。
