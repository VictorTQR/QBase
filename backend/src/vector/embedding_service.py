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
    async def embed_batch(
        cls, texts: list[str], model: Optional[str] = None
    ) -> list[list[float]]:
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
