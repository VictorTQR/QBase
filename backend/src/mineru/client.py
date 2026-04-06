import httpx
from loguru import logger
from typing import List, Dict, Any, Optional

from config import settings


class MinerUClient:
    """MinerU API 客户端封装"""

    def __init__(self):
        self.api_key = settings.MINERU_API_KEY
        self.base_url = settings.MINERU_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def batch_apply_upload_urls(
        self, files: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        申请批量上传 URL

        Args:
            files: 文件列表，每个文件包含 name 字段

        Returns:
            包含 batch_id 和 file_urls 的字典
        """
        url = f"{self.base_url}/api/v1/batch_parse/batch_apply_upload_urls"

        payload = {"files": files}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self.headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def upload_file(self, upload_url: str, file_content: bytes) -> bool:
        """
        上传文件到指定 URL

        Args:
            upload_url: 上传 URL
            file_content: 文件内容

        Returns:
            上传是否成功
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    upload_url,
                    content=file_content,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=60.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False

    async def create_batch_parse_task(
        self, batch_id: str, enable_formula: bool = True, enable_table: bool = True
    ) -> Dict[str, Any]:
        """
        创建批量解析任务

        Args:
            batch_id: 批次 ID
            enable_formula: 是否启用公式识别
            enable_table: 是否启用表格识别

        Returns:
            任务信息
        """
        url = f"{self.base_url}/api/v1/batch_parse/batch_parse"

        payload = {
            "batch_id": batch_id,
            "enable_formula": enable_formula,
            "enable_table": enable_table,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self.headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        获取批量解析任务状态

        Args:
            batch_id: 批次 ID

        Returns:
            任务状态信息
        """
        url = f"{self.base_url}/api/v1/batch_parse/batch_status"

        params = {"batch_id": batch_id}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self.headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def download_result(self, download_url: str) -> Optional[bytes]:
        """
        下载解析结果

        Args:
            download_url: 下载 URL

        Returns:
            文件内容，失败返回 None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, timeout=60.0)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"下载结果失败: {e}")
            return None


# 全局 MinerU 客户端实例
mineru_client = MinerUClient()
