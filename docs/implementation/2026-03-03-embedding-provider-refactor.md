# Embedding 服务多提供商重构 - 实施报告

**日期:** 2026-03-03  
**版本:** v1.0  
**状态:** ✅ 已完成

---

## 概述

本次重构将 QBase 的 Embedding 服务从单一 SiliconFlow 实现改造为支持多提供商的架构，采用与音频模块一致的 **Provider Pattern（提供者模式）**。

---

## 变更内容

### 新增文件

| 文件路径 | 描述 |
|---------|------|
| `backend/src/vector/providers/base.py` | EmbeddingProvider 抽象基类，定义接口契约 |
| `backend/src/vector/providers/__init__.py` | Providers 包初始化文件 |
| `backend/src/vector/providers/siliconflow.py` | SiliconFlowEmbeddingProvider 具体实现 |

### 修改文件

| 文件路径 | 变更内容 |
|---------|---------|
| `backend/src/config.py` | 新增 `EMBEDDING_PROVIDER` 配置项 |
| `backend/.env.example` | 新增向量搜索配置示例 |
| `backend/src/vector/embedding_service.py` | 重构为工厂模式，保持向后兼容 |

---

## 架构设计

### 目录结构

```
backend/src/vector/
├── providers/
│   ├── __init__.py
│   ├── base.py              # 抽象基类
│   └── siliconflow.py       # SiliconFlow 实现
├── embedding_service.py     # 工厂服务（向后兼容）
├── lancedb_service.py
├── text_chunker.py
└── schemas.py
```

### 设计模式

参考 `audio/providers/` 模块的成熟设计：

1. **抽象基类 (ABC)** - `EmbeddingProvider` 定义统一接口
2. **具体实现** - `SiliconFlowEmbeddingProvider` 实现特定提供商逻辑
3. **工厂模式** - `EmbeddingService` 根据配置创建对应提供商实例
4. **向后兼容** - 保持原有静态方法接口不变

---

## API 接口

### EmbeddingProvider 抽象基类

```python
class EmbeddingProvider(ABC):
    async def embed_text(self, text: str, model: Optional[str] = None) -> List[float]
    async def embed_batch(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]
    def get_embedding_dimension(self, model: str) -> int
    def validate_config(self) -> bool
    async def close(self)
```

### 配置项

```python
# config.py
EMBEDDING_PROVIDER: str = "siliconflow"
SILICONFLOW_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
```

---

## 扩展性说明

### 如何添加新的 Embedding 提供商

1. **创建新的 Provider 类**

```python
# backend/src/vector/providers/openai.py
from vector.providers.base import EmbeddingProvider

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: Optional[str] = None, ...):
        # 初始化配置
    
    async def embed_text(self, text: str, model: Optional[str] = None) -> List[float]:
        # 实现 OpenAI 调用逻辑
    
    # ... 实现其他抽象方法
```

2. **在工厂中注册**

```python
# backend/src/vector/embedding_service.py
@classmethod
def get_provider(cls) -> EmbeddingProvider:
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    
    if provider_name == "siliconflow":
        cls._provider = SiliconFlowEmbeddingProvider()
    elif provider_name == "openai":  # 新增
        cls._provider = OpenAIEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {provider_name}")
```

3. **更新导出**

```python
# backend/src/vector/providers/__init__.py
from .openai import OpenAIEmbeddingProvider  # 新增

__all__ = ["EmbeddingProvider", "SiliconFlowEmbeddingProvider", "OpenAIEmbeddingProvider"]
```

---

## 验证结果

| 验证项 | 状态 |
|-------|------|
| 模块导入测试 | ✅ 通过 |
| 配置加载测试 | ✅ 通过 |
| FastAPI 应用加载 | ✅ 通过 |
| 向后兼容性 | ✅ 保持 |

---

## 相关文档

- 计划文档: `.opencode/plans/2026-03-03-embedding-provider-refactor.md`
- 参考实现: `backend/src/audio/providers/`
