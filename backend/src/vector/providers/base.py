from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    """Embedding 提供商抽象基类"""

    @abstractmethod
    async def embed_text(self, text: str, model: Optional[str] = None) -> List[float]:
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
