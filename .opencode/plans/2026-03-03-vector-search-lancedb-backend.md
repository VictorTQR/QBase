# 向量搜索功能实施计划（LanceDB 后端版本）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 完善 QBase 的向量解析功能，采用后端 LanceDB + FastAPI 架构，实现基于语义的向量搜索。

**架构:** 
- 后端（FastAPI）: LanceDB 集成、文本分块、Embedding 生成（SiliconFlow）、向量 API
- 前端（Vue）: 调用后端 API、搜索面板增强、解析管理集成
- 策略: 混合索引（自动 + 手动）

**技术栈:** FastAPI, LanceDB, Python, Vue 3, Pinia, SiliconFlow Embedding API

---

## 任务清单

### 阶段一：后端 LanceDB 基础设施
1. 验证后端 LanceDB 依赖
2. 创建 LanceDB 服务模块
3. 创建文本分块器（Python）
4. 创建 Embedding 服务（Python）
5. 创建向量数据模型和 schemas

### 阶段二：后端向量 API
6. 创建向量索引 API 路由
7. 创建向量搜索 API 路由
8. 集成到解析任务流程（自动索引）
9. 添加向量统计和管理 API

### 阶段三：前端适配
10. 创建后端向量 API 客户端
11. 更新 useVectorStore（适配后端 API）
12. 增强 SearchPanel（向量搜索模式）
13. 更新 useSearchStore（调用后端 API）

### 阶段四：解析管理集成
14. 解析管理页面集成向量索引功能
15. 实现索引进度展示

---

## 详细任务

### Task 1: 验证后端 LanceDB 依赖

**文件:**
- Check: `backend/pyproject.toml` 或 `backend/requirements.txt`

**Step 1: 检查后端依赖配置**

查看 `backend/` 目录下的依赖配置文件，确认 lancedb 是否已安装。

**Step 2: 验证 LanceDB 可导入**

创建测试脚本验证：

```python
# backend/test_lancedb.py
import lancedb
print("LanceDB version:", lancedb.__version__)
```

运行: `cd backend && python test_lancedb.py`

**Step 3: 提交（如需要）**

如果需要添加依赖，更新配置文件并提交。

---

### Task 2: 创建 LanceDB 服务模块

**文件:**
- Create: `backend/src/vector/lancedb_service.py`
- Modify: `backend/main.py`

**Step 1: 实现 LanceDBService**

```python
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import lancedb
import pyarrow as pa
from loguru import logger

from config import settings


class LanceDBService:
    _instance: Optional['LanceDBService'] = None
    _db: Optional[lancedb.DBConnection] = None
    _table: Optional[lancedb.Table] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls):
        """初始化 LanceDB 连接和表"""
        if cls._db is not None:
            return

        lancedb_dir = Path(settings.STORAGE_DIR) / "lancedb"
        lancedb_dir.mkdir(parents=True, exist_ok=True)

        cls._db = lancedb.connect(str(lancedb_dir))
        logger.info(f"LanceDB connected at: {lancedb_dir}")

        cls._initialize_table()

    @classmethod
    def _initialize_table(cls):
        """初始化或打开文档向量表"""
        table_name = "document_chunks"

        if table_name in cls._db.table_names():
            cls._table = cls._db.open_table(table_name)
            logger.info(f"Opened existing table: {table_name}")
        else:
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("file_path", pa.string()),
                pa.field("file_name", pa.string()),
                pa.field("workspace_id", pa.string()),
                pa.field("chunk_index", pa.int32()),
                pa.field("content_type", pa.string()),
                pa.field("content", pa.string()),
                pa.field("start_char", pa.int32()),
                pa.field("end_char", pa.int32()),
                pa.field("created_at", pa.int64()),
                pa.field("vector", pa.list_(pa.float32(), 1024)),
            ])

            cls._table = cls._db.create_table(table_name, schema=schema)
            logger.info(f"Created new table: {table_name}")

    @classmethod
    def add_chunks(cls, chunks: List[Dict[str, Any]]):
        """添加文档分块"""
        if not chunks:
            return

        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append({
                "id": chunk["id"],
                "file_path": chunk["file_path"],
                "file_name": chunk["file_name"],
                "workspace_id": chunk.get("workspace_id", ""),
                "chunk_index": chunk["chunk_index"],
                "content_type": chunk.get("content_type", "text"),
                "content": chunk["content"],
                "start_char": chunk.get("start_char", 0),
                "end_char": chunk.get("end_char", len(chunk["content"])),
                "created_at": chunk.get("created_at", int(pa.compute.now().cast(pa.int64()).as_py() / 1000000)),
                "vector": chunk["vector"],
            })

        cls._table.add(formatted_chunks)
        logger.info(f"Added {len(formatted_chunks)} chunks to LanceDB")

    @classmethod
    def search(cls, query_vector: List[float], top_k: int = 10, 
               filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """向量搜索"""
        query = cls._table.search(query_vector).limit(top_k)

        if filter_expr:
            query = query.where(filter_expr)

        results = query.to_list()

        return [
            {
                "id": r["id"],
                "file_path": r["file_path"],
                "file_name": r["file_name"],
                "workspace_id": r["workspace_id"],
                "chunk_index": r["chunk_index"],
                "content": r["content"],
                "score": 1.0 - r["_distance"],
                "_distance": r["_distance"],
            }
            for r in results
        ]

    @classmethod
    def delete_by_file_path(cls, file_path: str):
        """删除指定文件的所有分块"""
        cls._table.delete(f"file_path = '{file_path}'")
        logger.info(f"Deleted chunks for file: {file_path}")

    @classmethod
    def clear_all(cls):
        """清空所有数据"""
        if "document_chunks" in cls._db.table_names():
            cls._db.drop_table("document_chunks")
            cls._initialize_table()
            logger.info("Cleared all data from LanceDB")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取统计信息"""
        count = cls._table.count_rows()
        return {
            "total_chunks": count,
            "table_name": "document_chunks"
        }


lancedb_service = LanceDBService()
```

**Step 2: 在启动时初始化**

更新 `backend/main.py` 的 startup_event：

```python
@app.on_event("startup")
async def startup_event():
    # ... 现有代码 ...
    
    # 初始化 LanceDB
    from vector.lancedb_service import lancedb_service
    lancedb_service.initialize()
    logger.info("LanceDB initialized")
```

**Step 3: 提交**

```bash
git add backend/src/vector/lancedb_service.py backend/main.py
git commit -m "feat: add LanceDB service module"
```

---

### Task 3: 创建文本分块器（Python）

**文件:**
- Create: `backend/src/vector/text_chunker.py`

**Step 1: 实现 TextChunker**

```python
import re
from typing import List, Dict, Any


class TextChunker:
    @staticmethod
    def split_by_semantic_boundary(text: str) -> List[str]:
        """按语义边界（标点、换行）分割"""
        sentences = re.split(r'(?<=[。！？\n])\s+', text)
        chunks = []
        current_chunk = ''

        for sentence in sentences:
            if not sentence.strip():
                continue
            if len(current_chunk) + len(sentence) > 500 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (' ' if current_chunk else '') + sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    @staticmethod
    def split_by_fixed_size(text: str, chunk_size: int = 512, 
                            chunk_overlap: int = 128) -> List[str]:
        """按固定大小分割"""
        chunks = []
        i = 0

        while i < len(text):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)
            i += chunk_size - chunk_overlap

        return chunks

    @staticmethod
    def chunk(text: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """混合分块策略"""
        options = options or {}
        chunk_size = options.get('chunk_size', 512)
        chunk_overlap = options.get('chunk_overlap', 128)
        use_semantic = options.get('use_semantic', True)

        raw_chunks = []
        if use_semantic:
            semantic_chunks = TextChunker.split_by_semantic_boundary(text)
            for sem_chunk in semantic_chunks:
                if len(sem_chunk) <= chunk_size:
                    raw_chunks.append(sem_chunk)
                else:
                    raw_chunks.extend(
                        TextChunker.split_by_fixed_size(sem_chunk, chunk_size, chunk_overlap)
                    )
        else:
            raw_chunks = TextChunker.split_by_fixed_size(text, chunk_size, chunk_overlap)

        result = []
        current_pos = 0
        for idx, content in enumerate(raw_chunks):
            start_idx = text.find(content, current_pos)
            if start_idx == -1:
                start_idx = current_pos
            end_idx = start_idx + len(content)

            result.append({
                'content': content,
                'index': idx,
                'start_char': start_idx,
                'end_char': end_idx
            })
            current_pos = end_idx - chunk_overlap

        return result
```

**Step 2: 提交**

```bash
git add backend/src/vector/text_chunker.py
git commit -m "feat: add TextChunker with hybrid chunking strategy"
```

---

### Task 4: 创建 Embedding 服务（Python）

**文件:**
- Create: `backend/src/vector/embedding_service.py`
- Modify: `backend/src/config.py`

**Step 1: 实现 EmbeddingService**

```python
import aiohttp
from typing import List, Optional
from loguru import logger

from config import settings


MODEL_DIMENSIONS = {
    'BAAI/bge-large-zh-v1.5': 1024,
    'BAAI/bge-m3': 1024
}


class EmbeddingService:
    @staticmethod
    def get_embedding_dimension(model: str) -> int:
        """获取模型维度"""
        dim = MODEL_DIMENSIONS.get(model)
        if dim is None:
            raise ValueError(f"Unknown embedding model: {model}")
        return dim

    @staticmethod
    async def embed_text(text: str, model: Optional[str] = None) -> List[float]:
        """生成单个文本的 embedding"""
        api_key = settings.SILICONFLOW_API_KEY
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not configured")

        model = model or 'BAAI/bge-large-zh-v1.5'
        base_url = settings.SILICONFLOW_API_BASE_URL.rstrip('/')

        url = f"{base_url}/v1/embeddings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        payload = {
            'model': model,
            'input': text
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Embedding API error: {response.status} - {error_text}")
                        raise ValueError(f"Embedding request failed: {response.status}")

                    data = await response.json()
                    return data['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Failed to embed text: {str(e)}")
            raise

    @staticmethod
    async def embed_batch(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """批量生成 embeddings"""
        embeddings = []
        for text in texts:
            embedding = await EmbeddingService.embed_text(text, model)
            embeddings.append(embedding)
        return embeddings
```

**Step 2: 更新 config.py**

添加 embedding 模型配置：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...

    # 向量配置
    SILICONFLOW_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    VECTOR_CHUNK_SIZE: int = 512
    VECTOR_CHUNK_OVERLAP: int = 128
    VECTOR_AUTO_INDEX: bool = False
```

**Step 3: 提交**

```bash
git add backend/src/vector/embedding_service.py backend/src/config.py
git commit -m "feat: add EmbeddingService for SiliconFlow API"
```

---

### Task 5: 创建向量数据模型和 schemas

**文件:**
- Create: `backend/src/vector/schemas.py`
- Create: `backend/src/vector/__init__.py`

**Step 1: 创建向量 schemas**

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class VectorIndexRequest(BaseModel):
    file_path: str
    file_name: str
    content: str
    workspace_id: Optional[str] = None
    content_type: Optional[str] = "text"
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class VectorIndexResponse(BaseModel):
    success: bool
    chunks_indexed: int
    message: str


class VectorSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10
    workspace_id: Optional[str] = None
    filter_expr: Optional[str] = None


class VectorSearchResult(BaseModel):
    id: str
    file_path: str
    file_name: str
    workspace_id: str
    chunk_index: int
    content: str
    score: float


class VectorSearchResponse(BaseModel):
    results: List[VectorSearchResult]
    total: int


class VectorStatsResponse(BaseModel):
    total_chunks: int
    table_name: str


class VectorDeleteRequest(BaseModel):
    file_path: str


class VectorOperationResponse(BaseModel):
    success: bool
    message: str
```

**Step 2: 创建 vector 包初始化文件**

`backend/src/vector/__init__.py`:

```python
from .lancedb_service import lancedb_service, LanceDBService
from .text_chunker import TextChunker
from .embedding_service import EmbeddingService
from .schemas import (
    VectorIndexRequest,
    VectorIndexResponse,
    VectorSearchRequest,
    VectorSearchResult,
    VectorSearchResponse,
    VectorStatsResponse,
    VectorDeleteRequest,
    VectorOperationResponse,
)

__all__ = [
    'lancedb_service',
    'LanceDBService',
    'TextChunker',
    'EmbeddingService',
    'VectorIndexRequest',
    'VectorIndexResponse',
    'VectorSearchRequest',
    'VectorSearchResult',
    'VectorSearchResponse',
    'VectorStatsResponse',
    'VectorDeleteRequest',
    'VectorOperationResponse',
]
```

**Step 3: 提交**

```bash
git add backend/src/vector/schemas.py backend/src/vector/__init__.py
git commit -m "feat: add vector data models and schemas"
```

---

### Task 6: 创建向量索引 API 路由

**文件:**
- Create: `backend/src/api/vector.py`
- Modify: `backend/main.py`

**Step 1: 实现向量索引 API**

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger

from vector import (
    lancedb_service,
    TextChunker,
    EmbeddingService,
    VectorIndexRequest,
    VectorIndexResponse,
    VectorDeleteRequest,
    VectorOperationResponse,
    VectorStatsResponse,
)
from config import settings

router = APIRouter(prefix="/api/vector", tags=["Vector"])


@router.post("/index", response_model=VectorIndexResponse)
async def index_document(request: VectorIndexRequest):
    """索引单个文档"""
    try:
        chunk_size = request.chunk_size or settings.VECTOR_CHUNK_SIZE
        chunk_overlap = request.chunk_overlap or settings.VECTOR_CHUNK_OVERLAP

        chunks = TextChunker.chunk(request.content, {
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'use_semantic': True
        })

        indexed_chunks = []
        for chunk in chunks:
            embedding = await EmbeddingService.embed_text(
                chunk['content'],
                settings.SILICONFLOW_EMBEDDING_MODEL
            )

            chunk_id = f"{request.file_path}_chunk_{chunk['index']}"
            indexed_chunks.append({
                'id': chunk_id,
                'file_path': request.file_path,
                'file_name': request.file_name,
                'workspace_id': request.workspace_id or '',
                'chunk_index': chunk['index'],
                'content_type': request.content_type or 'text',
                'content': chunk['content'],
                'start_char': chunk['start_char'],
                'end_char': chunk['end_char'],
                'vector': embedding,
            })

        lancedb_service.delete_by_file_path(request.file_path)
        lancedb_service.add_chunks(indexed_chunks)

        return VectorIndexResponse(
            success=True,
            chunks_indexed=len(indexed_chunks),
            message=f"Successfully indexed {len(indexed_chunks)} chunks"
        )
    except Exception as e:
        logger.error(f"Failed to index document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete", response_model=VectorOperationResponse)
async def delete_document_chunks(request: VectorDeleteRequest):
    """删除指定文件的向量索引"""
    try:
        lancedb_service.delete_by_file_path(request.file_path)
        return VectorOperationResponse(
            success=True,
            message=f"Deleted chunks for file: {request.file_path}"
        )
    except Exception as e:
        logger.error(f"Failed to delete document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=VectorStatsResponse)
async def get_vector_stats():
    """获取向量索引统计"""
    try:
        stats = lancedb_service.get_stats()
        return VectorStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get vector stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=VectorOperationResponse)
async def clear_all_vectors():
    """清空所有向量索引"""
    try:
        lancedb_service.clear_all()
        return VectorOperationResponse(
            success=True,
            message="All vector data cleared"
        )
    except Exception as e:
        logger.error(f"Failed to clear vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 注册路由到 main.py**

```python
from api.vector import router as vector_router

app.include_router(vector_router)
```

**Step 3: 提交**

```bash
git add backend/src/api/vector.py backend/main.py
git commit -m "feat: add vector index API routes"
```

---

### Task 7: 创建向量搜索 API 路由

**文件:**
- Modify: `backend/src/api/vector.py`

**Step 1: 添加搜索端点**

在 `backend/src/api/vector.py` 中添加：

```python
from vector import (
    # ... 现有导入 ...
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)


@router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(request: VectorSearchRequest):
    """向量搜索"""
    try:
        query_embedding = await EmbeddingService.embed_text(
            request.query,
            settings.SILICONFLOW_EMBEDDING_MODEL
        )

        filter_expr = request.filter_expr
        if request.workspace_id:
            workspace_filter = f"workspace_id = '{request.workspace_id}'"
            if filter_expr:
                filter_expr = f"({filter_expr}) AND ({workspace_filter})"
            else:
                filter_expr = workspace_filter

        results = lancedb_service.search(
            query_embedding,
            top_k=request.top_k or 10,
            filter_expr=filter_expr
        )

        search_results = [
            VectorSearchResult(**r)
            for r in results
        ]

        return VectorSearchResponse(
            results=search_results,
            total=len(search_results)
        )
    except Exception as e:
        logger.error(f"Failed to search vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 提交**

```bash
git add backend/src/api/vector.py
git commit -m "feat: add vector search API endpoint"
```

---

### Task 8: 集成到解析任务流程（自动索引）

**文件:**
- Modify: `backend/src/mineru/task_manager.py`

**Step 1: 在解析完成后触发自动索引**

当解析任务状态变为 `done` 时，如果配置了自动索引，则触发向量索引。

**Step 2: 提交**

```bash
git add backend/src/mineru/task_manager.py
git commit -m "feat: auto-index vectors when parse completes"
```

---

### Task 9: 添加向量统计和管理 API

（已包含在 Task 6 中）

---

### Task 10: 创建后端向量 API 客户端（前端）

**文件:**
- Create: `app/src/api/vectorBackend.js`

**Step 1: 实现向量 API 客户端**

```javascript
import { backendFetch } from '@/utils/backend'

export class VectorBackendApi {
  static async indexDocument(params) {
    return await backendFetch('/api/vector/index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
  }

  static async searchVectors(params) {
    return await backendFetch('/api/vector/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
  }

  static async deleteDocumentChunks(filePath) {
    return await backendFetch('/api/vector/delete', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath })
    })
  }

  static async getVectorStats() {
    return await backendFetch('/api/vector/stats')
  }

  static async clearAllVectors() {
    return await backendFetch('/api/vector/clear', {
      method: 'POST'
    })
  }
}
```

**Step 2: 提交**

```bash
git add app/src/api/vectorBackend.js
git commit -m "feat: add vector backend API client"
```

---

### Task 11: 更新 useVectorStore（适配后端 API）

**文件:**
- Modify: `app/src/stores/vector.js`

**Step 1: 更新 useVectorStore**

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { VectorBackendApi } from '@/api/vectorBackend'

export const useVectorStore = defineStore(
  'vector',
  () => {
    const isIndexing = ref(false)
    const indexingProgress = ref(0)
    const indexingTotal = ref(0)
    const currentIndexingFile = ref('')
    const error = ref(null)
    const stats = ref(null)

    async function indexDocument(filePath, fileName, content, workspaceId) {
      isIndexing.value = true
      currentIndexingFile.value = fileName
      error.value = null

      try {
        const result = await VectorBackendApi.indexDocument({
          file_path: filePath,
          file_name: fileName,
          content,
          workspace_id: workspaceId
        })
        await loadStats()
        return result
      } catch (err) {
        error.value = err.message
        throw err
      } finally {
        isIndexing.value = false
        currentIndexingFile.value = ''
      }
    }

    async function searchVectors(query, topK = 10, workspaceId = null) {
      return await VectorBackendApi.searchVectors({
        query,
        top_k: topK,
        workspace_id: workspaceId
      })
    }

    async function deleteDocumentChunks(filePath) {
      return await VectorBackendApi.deleteDocumentChunks(filePath)
    }

    async function loadStats() {
      stats.value = await VectorBackendApi.getVectorStats()
      return stats.value
    }

    async function clearAll() {
      const result = await VectorBackendApi.clearAllVectors()
      stats.value = null
      return result
    }

    return {
      isIndexing,
      indexingProgress,
      indexingTotal,
      currentIndexingFile,
      error,
      stats,
      indexDocument,
      searchVectors,
      deleteDocumentChunks,
      loadStats,
      clearAll
    }
  },
  {
    persist: {
      key: 'qbase-vector',
      paths: []
    }
  }
)
```

**Step 2: 提交**

```bash
git add app/src/stores/vector.js
git commit -m "feat: update useVectorStore for backend API"
```

---

### Task 12: 增强 SearchPanel（向量搜索模式）

**文件:**
- Modify: `app/src/components/SearchPanel.vue`

**Step 1: 添加搜索模式切换**

在搜索范围选择器下方添加搜索模式切换：

```vue
<div class="search-mode">
  <el-radio-group v-model="searchMode" size="small" @change="handleModeChange">
    <el-radio-button value="fulltext">全文</el-radio-button>
    <el-radio-button value="vector">向量</el-radio-button>
    <el-radio-button value="hybrid">混合</el-radio-button>
  </el-radio-group>
</div>
```

**Step 2: 更新结果展示**

显示相似度分数：

```vue
<div class="result-name">
  <span v-html="highlightText(result.name, searchStore.query)"></span>
  <el-tag v-if="result.matchType === 'name'" size="small" type="info">文件名</el-tag>
  <el-tag v-else-if="result.matchType === 'content'" size="small" type="success">内容</el-tag>
  <el-tag v-if="result.score !== undefined" size="small" type="warning">
    {{ (result.score * 100).toFixed(0) }}%
  </el-tag>
</div>
```

**Step 3: 添加样式**

```css
.search-mode {
  padding: 8px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: center;
}
```

**Step 4: 更新 script**

```javascript
const searchMode = ref('fulltext')

function handleModeChange() {
  searchStore.setSearchMode(searchMode.value)
  if (searchStore.query) {
    searchStore.performSearch()
  }
}

watch(
  () => searchStore.isPanelOpen,
  async (isOpen) => {
    if (isOpen) {
      await nextTick()
      inputRef.value?.focus()
      searchQuery.value = searchStore.query
      searchScope.value = searchStore.searchScope
      searchMode.value = searchStore.searchMode
    }
  },
)
```

**Step 5: 提交**

```bash
git add app/src/components/SearchPanel.vue
git commit -m "feat: enhance SearchPanel with vector search mode"
```

---

### Task 13: 更新 useSearchStore（调用后端 API）

**文件:**
- Modify: `app/src/stores/search.js`

**Step 1: 更新 useSearchStore**

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useWorkspaceStore } from './workspace'
import { useVectorStore } from './vector'

export const useSearchStore = defineStore(
  'search',
  () => {
    const query = ref('')
    const results = ref([])
    const isLoading = ref(false)
    const error = ref(null)
    const isPanelOpen = ref(false)
    const searchScope = ref('all')
    const searchMode = ref('fulltext')
    const selectedIndex = ref(0)

    const workspaceStore = useWorkspaceStore()
    const vectorStore = useVectorStore()

    const hasResults = computed(() => results.value.length > 0)
    const isSearching = computed(() => isLoading.value && query.value.length > 0)

    function openPanel() {
      isPanelOpen.value = true
      selectedIndex.value = 0
    }

    function closePanel() {
      isPanelOpen.value = false
      query.value = ''
      results.value = []
      error.value = null
      selectedIndex.value = 0
    }

    function setQuery(newQuery) {
      query.value = newQuery
      selectedIndex.value = 0
    }

    function setSearchScope(scope) {
      searchScope.value = scope
    }

    function setSearchMode(mode) {
      searchMode.value = mode
    }

    function selectPreviousResult() {
      if (results.value.length > 0) {
        selectedIndex.value =
          (selectedIndex.value - 1 + results.value.length) % results.value.length
      }
    }

    function selectNextResult() {
      if (results.value.length > 0) {
        selectedIndex.value = (selectedIndex.value + 1) % results.value.length
      }
    }

    function getSelectedResult() {
      return results.value[selectedIndex.value] || null
    }

    async function performFulltextSearch() {
      const foldersToSearch =
        searchScope.value === 'all'
          ? workspaceStore.folders
          : workspaceStore.folders.filter((f) => f.id === searchScope.value)

      const allResults = []

      for (const folder of foldersToSearch) {
        const result = await window.electronAPI.searchFiles(folder.path, query.value)
        if (result.success) {
          allResults.push(...result.results)
        } else {
          console.error(`搜索文件夹 ${folder.name} 失败:`, result.error)
        }
      }

      return allResults
    }

    async function performVectorSearch() {
      const workspaceId = searchScope.value === 'all' ? null : searchScope.value
      const response = await vectorStore.searchVectors(query.value, 10, workspaceId)

      return response.results.map(r => ({
        id: r.file_path,
        name: r.file_name,
        path: r.file_path,
        snippet: r.content,
        matchType: 'vector',
        score: r.score,
        chunkIndex: r.chunk_index
      }))
    }

    async function performHybridSearch() {
      const [fulltextResults, vectorResults] = await Promise.all([
        performFulltextSearch(),
        performVectorSearch()
      ])

      const merged = new Map()

      fulltextResults.forEach(r => {
        merged.set(r.id, { ...r, ftScore: 1 })
      })

      vectorResults.forEach(r => {
        const existing = merged.get(r.id)
        if (existing) {
          existing.score = (existing.score || 0) + r.score * 0.7
          existing.snippet = existing.snippet || r.snippet
        } else {
          merged.set(r.id, { ...r, score: r.score * 0.7 })
        }
      })

      return Array.from(merged.values()).sort((a, b) => (b.score || b.ftScore) - (a.score || a.ftScore))
    }

    async function performSearch() {
      if (!query.value.trim()) {
        results.value = []
        return
      }

      isLoading.value = true
      error.value = null
      results.value = []

      try {
        if (searchMode.value === 'vector') {
          results.value = await performVectorSearch()
        } else if (searchMode.value === 'hybrid') {
          results.value = await performHybridSearch()
        } else {
          results.value = await performFulltextSearch()
        }
      } catch (err) {
        error.value = err.message
        console.error('搜索失败:', err)
      } finally {
        isLoading.value = false
      }
    }

    function clearResults() {
      results.value = []
      error.value = null
      selectedIndex.value = 0
    }

    return {
      query,
      results,
      isLoading,
      error,
      isPanelOpen,
      searchScope,
      searchMode,
      selectedIndex,
      hasResults,
      isSearching,
      openPanel,
      closePanel,
      setQuery,
      setSearchScope,
      setSearchMode,
      selectPreviousResult,
      selectNextResult,
      getSelectedResult,
      performSearch,
      clearResults,
    }
  },
  {
    persist: {
      key: 'qbase-search',
      paths: ['searchScope', 'searchMode'],
    },
  },
)
```

**Step 2: 提交**

```bash
git add app/src/stores/search.js
git commit -m "feat: update useSearchStore to call backend vector API"
```

---

### Task 14: 解析管理页面集成向量索引功能

**文件:**
- Modify: `app/src/views/ParseManagement.vue`
- Modify: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1: 在 ParseDocumentsView 添加向量索引按钮**

在文档卡片操作区域添加"索引向量"按钮，以及批量索引功能。

**Step 2: 在 ParseManagement 集成索引进度展示**

添加索引进度状态展示。

**Step 3: 提交**

```bash
git add app/src/views/ParseManagement.vue app/src/components/parse/ParseDocumentsView.vue
git commit -m "feat: integrate vector indexing into parse management"
```

---

### Task 15: 实现索引进度展示

（根据需要实现）

---

## 执行选项

计划已保存到 `.opencode/plans/2026-03-03-vector-search-lancedb-backend.md`

两个执行选项：

**1. Subagent-Driven（本会话）** - 我为每个任务分派新的子代理，任务间进行代码审查

**2. Parallel Session（单独会话）** - 打开新会话使用 executing-plans

选择哪种方式？
