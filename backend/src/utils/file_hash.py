import hashlib
from pathlib import Path
from typing import Union
import aiofiles
from loguru import logger


async def compute_file_hash(file_path: Union[str, Path]) -> str:
    """计算文件的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()

    async with aiofiles.open(file_path, "rb") as f:
        # 分块读取文件，避免大文件内存溢出
        chunk_size = 8192
        while chunk := await f.read(chunk_size):
            sha256_hash.update(chunk)

    file_hash = sha256_hash.hexdigest()
    logger.debug(f"文件 {file_path} 哈希: {file_hash}")
    return file_hash


def compute_bytes_hash(content: bytes) -> str:
    """计算字节内容的 SHA-256 哈希值"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()
