from abc import ABC, abstractmethod
from typing import Optional


class ASRProvider(ABC):
    """ASR 提供商抽象基类"""

    @abstractmethod
    async def transcribe(
        self, audio_file_path: str, model: Optional[str] = None
    ) -> str:
        """
        转录音频文件为文本

        Args:
            audio_file_path: 音频文件路径
            model: 模型名称（可选，覆盖默认配置）

        Returns:
            转录的文本内容

        Raises:
            Exception: 转录失败时抛出异常
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass
