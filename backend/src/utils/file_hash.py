import hashlib
from pathlib import Path
from loguru import logger


def compute_file_hash(file_path: str, length: int = 16) -> str:
    """
    计算文件的 SHA-256 哈希

    Args:
        file_path: 文件路径
        length: 返回的哈希长度（默认前16位）

    Returns:
        哈希字符串
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        full_hash = sha256_hash.hexdigest()
        return full_hash[:length]
    except Exception as e:
        logger.error(f"计算文件哈希失败 {file_path}: {e}")
        raise


def compute_short_hash(content: bytes, length: int = 16) -> str:
    """
    计算内容的短哈希

    Args:
        content: 字节内容
        length: 返回的哈希长度

    Returns:
        哈希字符串
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()[:length]
