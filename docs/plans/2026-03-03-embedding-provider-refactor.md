# Embedding 服务多提供商重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 重构 Embedding 服务，采用提供者模式（Provider Pattern），支持轻松切换不同的 embedding 提供商。

**架构:** 参考 `audio/providers/` 模块的设计，创建抽象基类 + 具体实现 + 工厂模式的架构。

**技术栈:** Python, ABC (Abstract Base Classes), FastAPI

---

## 任务清单

### 阶段一：基础设施搭建
1. 创建 providers 目录结构
2. 创建 EmbeddingProvider 抽象基类
3. 创建 providers 包初始化文件

### 阶段二：实现 SiliconFlow 提供商
4. 创建 SiliconFlowEmbeddingProvider
5. 移植现有 embedding 逻辑
6. 实现配置验证和资源管理

### 阶段三：更新配置系统
7. 更新 config.py 添加提供商选择配置
8. 更新 .env.example 示例配置

### 阶段四：重构 EmbeddingService
9. 重构 embedding_service.py 使用工厂模式
10. 保持向后兼容性

### 阶段五：更新调用方
11. 更新 api/vector.py 使用新服务
12. 更新 vector/__init__.py 导出

### 阶段六：测试和验证
13. 验证功能正常
14. 更新文档

---

## 详细任务

### Task 1: 创建 providers 目录结构

**文件:**
- Create: `backend/src/vector/providers/` (directory)

**Step 1: 创建目录**

```bash
mkdir -p backend/src/vector/providers
```

**Step 2: 验证目录创建**

```bash
ls -la backend/src/vector/
```

Expected: 看到 `providers/` 目录

**Step 3: 提交**

```bash
git add backend/src/vector/providers
git commit -m "feat: create vector providers directory"
```

---

### Task 2: 创建 EmbeddingProvider 抽象基类

**文件:**
- Create: `backend/src/vector/providers/base.py`
- Reference: `backend/src/audio/providers/base.py`

**Step 1: 编写抽象基类**

```python
from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    """Embedding 提供商抽象基类"""

    @abstractmethod
    async def embed_text(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """
        生成单个文本的 embedding

        Args:
            text: 输入文本
            model: 模型名称（可选，覆盖默认配置）

        Returns:
            embedding 向量列表

        Raises:
            Exception: 生成失败时抛出异常
        """
        pass

    @abstractmethod
    async def embed_batch(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """
        批量生成 embeddings

        Args:
            texts: 输入文本列表
            model: 模型名称（可选，覆盖默认配置）

        Returns:
            embedding 向量列表的列表
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self, model: str) -> int:
        """
        获取模型的 embedding 维度

        Args:
            model: 模型名称

        Returns:
            维度数量
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass

    async def close(self):
        """清理资源（可选实现）"""
        pass
```

**Step 2: 提交**

```bash
git add backend/src/vector/providers/base.py
git commit -m "feat: add EmbeddingProvider abstract base class"
```

---

### Task 3: 创建 providers 包初始化文件

**文件:**
- Create: `backend/src/vector/providers/__init__.py`
- Reference: `backend/src/audio/providers/__init__.py`

**Step 1: 编写初始化文件**

```python
from .base import EmbeddingProvider
from .siliconflow import SiliconFlowEmbeddingProvider

__all__ = ["EmbeddingProvider", "SiliconFlowEmbeddingProvider"]
```

**Step 2: 提交**

```bash
git add backend/src/vector/providers/__init__.py
git commit -m "feat: add vector providers package init"
```

---

### Task 4: 创建 SiliconFlowEmbeddingProvider

**文件:**
- Create: `backend/src/vector/providers/siliconflow.py`
- Reference: `backend/src/audio/providers/siliconflow.py`
- Reference: `backend/src/vector/embedding_service.py` (现有代码)

**Step 1: 编写 SiliconFlow 提供商实现**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import aiohttp
from typing import List, Optional
from loguru import logger

from vector.providers.base import EmbeddingProvider
from config import settings


MODEL_DIMENSIONS = {
    'BAAI/bge-large-zh-v1.5': 1024,
    'BAAI/bge-m3': 1024
}


class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """硅基流动 Embedding 提供商实现"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.SILICONFLOW_API_KEY
        self.base_url = base_url or settings.SILICONFLOW_API_BASE_URL
        self.model = model or settings.SILICONFLOW_EMBEDDING_MODEL
        self._client: Optional[aiohttp.ClientSession] = None

    async def _get_client(self) -> aiohttp.ClientSession:
        if self._client is None:
            self._client = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=60.0,
            )
        return self._client

    async def embed_text(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        use_model = model or self.model
        client = await self._get_client()

        url = f"{self.base_url.rstrip('/')}/v1/embeddings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            'model': use_model,
            'input': text
        }

        try:
            async with client.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Embedding API error: {response.status} - {error_text}")
                    raise ValueError(f"Embedding request failed: {response.status}")

                data = await response.json()
                return data['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Failed to embed text: {str(e)}")
            raise

    async def embed_batch(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text, model)
            embeddings.append(embedding)
        return embeddings

    def get_embedding_dimension(self, model: str) -> int:
        dim = MODEL_DIMENSIONS.get(model)
        if dim is None:
            raise ValueError(f"Unknown embedding model: {model}")
        return dim

    def validate_config(self) -> bool:
        if not self.api_key:
            logger.error("硅基流动 API Key 未配置")
            return False
        if not self.base_url:
            logger.error("硅基流动 API Base URL 未配置")
            return False
        return True

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
```

**Step 2: 提交**

```bash
git add backend/src/vector/providers/siliconflow.py
git commit -m "feat: add SiliconFlowEmbeddingProvider"
```

---

### Task 5: 更新 config.py 添加提供商配置

**文件:**
- Modify: `backend/src/config.py`

**Step 1: 添加提供商选择配置**

在 `# 向量配置` 部分修改：

```python
    # 向量配置
    EMBEDDING_PROVIDER: str = "siliconflow"
    SILICONFLOW_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    VECTOR_CHUNK_SIZE: int = 512
    VECTOR_CHUNK_OVERLAP: int = 128
    VECTOR_AUTO_INDEX: bool = False
```

**Step 2: 提交**

```bash
git add backend/src/config.py
git commit -m "feat: add EMBEDDING_PROVIDER config option"
```

---

### Task 6: 更新 .env.example

**文件:**
- Modify: `backend/.env.example`

**Step 1: 添加向量配置示例**

在文件末尾添加：

```
# 向量搜索配置
EMBEDDING_PROVIDER=siliconflow
SILICONFLOW_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

**Step 2: 提交**

```bash
git add backend/.env.example
git commit -m "docs: update .env.example with embedding provider config"
```

---

### Task 7: 重构 embedding_service.py 使用工厂模式

**文件:**
- Modify: `backend/src/vector/embedding_service.py`

**Step 1: 重写 embedding_service.py**

```python
from typing import Optional
from loguru import logger

from config import settings
from vector.providers import (
    EmbeddingProvider,
    SiliconFlowEmbeddingProvider,
)


class EmbeddingService:
    _provider: Optional[EmbeddingProvider] = None

    @classmethod
    def get_provider(cls) -> EmbeddingProvider:
        """获取当前配置的 embedding 提供商"""
        if cls._provider is None:
            provider_name = settings.EMBEDDING_PROVIDER.lower()
            
            if provider_name == "siliconflow":
                cls._provider = SiliconFlowEmbeddingProvider()
            else:
                raise ValueError(f"Unknown embedding provider: {provider_name}")
            
            if not cls._provider.validate_config():
                logger.warning(f"Embedding provider config validation failed")
        
        return cls._provider

    @classmethod
    async def embed_text(cls, text: str, model: Optional[str] = None) -> list[float]:
        """生成单个文本的 embedding（向后兼容接口）"""
        provider = cls.get_provider()
        return await provider.embed_text(text, model)

    @classmethod
    async def embed_batch(cls, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        """批量生成 embeddings（向后兼容接口）"""
        provider = cls.get_provider()
        return await provider.embed_batch(texts, model)

    @classmethod
    def get_embedding_dimension(cls, model: str) -> int:
        """获取模型维度（向后兼容接口）"""
        provider = cls.get_provider()
        return provider.get_embedding_dimension(model)

    @classmethod
    async def close(cls):
        """关闭 provider 连接"""
        if cls._provider:
            await cls._provider.close()
            cls._provider = None
```

**Step 2: 提交**

```bash
git add backend/src/vector/embedding_service.py
git commit -m "refactor: EmbeddingService to use provider factory pattern"
```

---

### Task 8: 更新 api/vector.py （验证兼容性）

**文件:**
- Verify: `backend/src/api/vector.py`

**Step 1: 确认无需修改**

由于我们保持了 `EmbeddingService` 的向后兼容接口（相同的静态方法签名），`api/vector.py` 应该无需修改即可工作。

**Step 2: 验证导入**

检查 `api/vector.py` 中的导入：

```python
from vector import (
    lancedb_service,
    TextChunker,
    EmbeddingService,  # 这个应该仍然有效
    ...
)
```

**Step 3: 提交（如需要）**

如果无需修改，跳过提交。

---

### Task 9: 更新 vector/__init__.py

**文件:**
- Modify: `backend/src/vector/__init__.py`

**Step 1: 更新导出（可选）**

保持原样，因为我们保持了向后兼容性：

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

**Step 2: （可选）添加 providers 导出**

如果需要导出 providers，可以添加：

```python
from .providers import EmbeddingProvider, SiliconFlowEmbeddingProvider

# 在 __all__ 中添加:
#    'EmbeddingProvider',
#    'SiliconFlowEmbeddingProvider',
```

**Step 3: 提交**

```bash
git add backend/src/vector/__init__.py
git commit -m "refactor: update vector package exports"
```

---

### Task 10: 测试和验证

**文件:**
- Test: 运行后端并验证

**Step 1: 测试导入**

```bash
cd backend
uv run python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from vector.embedding_service import EmbeddingService
from vector.providers import EmbeddingProvider, SiliconFlowEmbeddingProvider
print('All imports successful!')
"
```

Expected: "All imports successful!"

**Step 2: 检查配置加载**

```bash
cd backend
uv run python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from config import settings
print(f'EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}')
print(f'SILICONFLOW_EMBEDDING_MODEL: {settings.SILICONFLOW_EMBEDDING_MODEL}')
"
```

**Step 3: 启动后端检查**

```bash
cd backend
uv run python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from main import app
print('FastAPI app loaded successfully!')
"
```

Expected: "FastAPI app loaded successfully!"

---

## 执行选项

计划已保存到 `.opencode/plans/2026-03-03-embedding-provider-refactor.md`

两个执行选项：

**1. Subagent-Driven（本会话）** - 我为每个任务分派新的子代理，任务间进行代码审查

**2. Parallel Session（单独会话）** - 打开新会话使用 executing-plans

选择哪种方式？
