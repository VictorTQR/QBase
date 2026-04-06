import aiohttp
from typing import List, Optional
from loguru import logger

from ..providers.base import EmbeddingProvider
from ...config import settings


MODEL_DIMENSIONS = {"BAAI/bge-large-zh-v1.5": 1024, "BAAI/bge-m3": 1024}


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
                timeout=aiohttp.ClientTimeout(total=60.0),
            )
        return self._client

    async def embed_text(self, text: str, model: Optional[str] = None) -> List[float]:
        use_model = model or self.model
        client = await self._get_client()

        url = f"{self.base_url.rstrip('/')}/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"model": use_model, "input": text}

        try:
            async with client.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Embedding API error: {response.status} - {error_text}"
                    )
                    raise ValueError(f"Embedding request failed: {response.status}")

                data = await response.json()
                return data["data"][0]["embedding"]
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
