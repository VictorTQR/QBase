from pathlib import Path
from typing import Set

# 支持的音频扩展名
SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {
    ".mp3",
    ".wav",
    ".ogg",
    ".m4a",
    ".flac",
    ".aac",
    ".wma",
    ".opus",
    ".webm",
}


def is_audio_file(file_path: str) -> bool:
    """判断是否为音频文件"""
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_AUDIO_EXTENSIONS


def merge_transcriptions(chunk_transcriptions: list) -> str:
    """
    合并多个分块的转录文本

    Args:
        chunk_transcriptions: [(start_time, end_time, text), ...]

    Returns:
        合并后的文本
    """
    # 按开始时间排序
    sorted_chunks = sorted(chunk_transcriptions, key=lambda x: x[0])

    # 简单拼接
    merged = []
    for _, _, text in sorted_chunks:
        if text and text.strip():
            merged.append(text.strip())

    return "\n\n".join(merged)
