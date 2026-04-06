import httpx
from loguru import logger
from typing import List, Dict, Any, Optional

from ..config import settings


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
        self, files: List[Dict[str, Any]], model_version: str = "vlm"
    ) -> Dict[str, Any]:
        """
        批量申请上传链接

        Args:
            files: 文件列表，每个文件包含 name 和可选的 data_id
            model_version: 模型版本，默认为 "vlm"

        Returns:
            包含 batch_id 和 file_urls 的字典
        """
        url = f"{self.base_url}/api/v4/file-urls/batch"
        data = {"files": files, "model_version": model_version}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=data)
                response.raise_for_status()
                result = response.json()

                if result.get("code") == 0:
                    logger.info(
                        f"批量申请上传链接成功，batch_id: {result['data']['batch_id']}"
                    )
                    return result["data"]
                else:
                    logger.error(f"批量申请上传链接失败: {result.get('msg')}")
                    raise Exception(f"批量申请上传链接失败: {result.get('msg')}")
        except Exception as e:
            logger.error(f"批量申请上传链接请求异常: {str(e)}")
            raise

    async def upload_file(self, upload_url: str, file_content: bytes) -> bool:
        """
        上传文件到指定 URL

        Args:
            upload_url: 上传链接
            file_content: 文件内容（字节）

        Returns:
            上传是否成功
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(upload_url, content=file_content)

                if response.status_code == 200:
                    logger.info(f"文件上传成功")
                    return True
                else:
                    logger.error(f"文件上传失败，状态码: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"文件上传请求异常: {str(e)}")
            raise

    async def batch_query_results(self, batch_id: str) -> Dict[str, Any]:
        """
        批量查询任务结果

        Args:
            batch_id: 批量任务 ID

        Returns:
            批量任务结果
        """
        url = f"{self.base_url}/api/v4/extract-results/batch/{batch_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()

                if result.get("code") == 0:
                    logger.info(f"批量查询任务结果成功")
                    return result["data"]
                else:
                    logger.error(f"批量查询任务结果失败: {result.get('msg')}")
                    raise Exception(f"批量查询任务结果失败: {result.get('msg')}")
        except Exception as e:
            logger.error(f"批量查询任务结果请求异常: {str(e)}")
            raise

    async def download_zip(self, zip_url: str) -> bytes:
        """
        下载结果 ZIP 文件

        Args:
            zip_url: ZIP 文件下载链接

        Returns:
            ZIP 文件内容（字节）
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(zip_url)
                response.raise_for_status()

                logger.info(f"ZIP 文件下载成功")
                return response.content
        except Exception as e:
            logger.error(f"ZIP 文件下载请求异常: {str(e)}")
            raise


mineru_client = MinerUClient()
