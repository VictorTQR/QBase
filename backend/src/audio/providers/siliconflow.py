import httpx
from typing import Optional
from loguru import logger

from audio.providers.base import ASRProvider
from config import settings


class SiliconFlowASRProvider(ASRProvider):
    """硅基流动 ASR 提供商实现"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.SILICONFLOW_API_KEY
        self.base_url = base_url or settings.SILICONFLOW_API_BASE_URL
        self.model = model or settings.SILICONFLOW_ASR_MODEL

    async def transcribe(
        self, audio_path: str, language: str = "zh"
    ) -> dict:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            转录结果
        """
        url = f"{self.base_url}/v1/audio/transcriptions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # 读取音频文件
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        files = {
            "file": ("audio.wav", audio_data, "audio/wav"),
            "model": (None, self.model),
            "language": (None, language),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=headers, files=files, timeout=300.0
            )
            response.raise_for_status()
            result = response.json()

        return {
            "text": result.get("text", ""),
            "model": self.model,
        }

    async def transcribe_chunk(
        self, chunk_path: str, chunk_id: str
    ) -> dict:
        """
        转录单个音频分块

        Args:
            chunk_path: 分块文件路径
            chunk_id: 分块 ID

        Returns:
            转录结果
        """
        result = await self.transcribe(chunk_path)
        return {
            "chunk_id": chunk_id,
            "text": result["text"],
            "model": result["model"],
        }
