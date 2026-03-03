import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=300.0,  # 5 分钟超时
                follow_redirects=True,
            )
        return self._client

    async def transcribe(
        self, audio_file_path: str, model: Optional[str] = None
    ) -> str:
        use_model = model or self.model
        client = await self._get_client()

        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")

        logger.info(f"开始转录音频: {audio_file_path}, 模型: {use_model}")

        with open(audio_file_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/mpeg")}
            data = {"model": use_model}
            headers = {"Authorization": f"Bearer {self.api_key}"}

            response = await client.post(
                "/v1/audio/transcriptions", files=files, data=data, headers=headers
            )

            if response.status_code != 200:
                logger.error(
                    f"硅基流动 API 错误: {response.status_code} - {response.text}"
                )
                raise Exception(f"转录失败: {response.status_code} - {response.text}")

            result = response.json()
            transcription = result.get("text", "")
            logger.info(f"转录完成，文本长度: {len(transcription)}")
            return transcription

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
            await self._client.aclose()
            self._client = None
