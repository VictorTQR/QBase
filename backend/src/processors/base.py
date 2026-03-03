from abc import ABC, abstractmethod
from typing import Any, Optional


class FileProcessor(ABC):
    """文件处理器抽象基类"""

    @abstractmethod
    async def process(self, file_path: str, config: Optional[dict] = None) -> Any:
        """
        处理文件

        Args:
            file_path: 文件路径
            config: 配置参数

        Returns:
            处理结果
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """判断是否支持该文件类型"""
        pass
