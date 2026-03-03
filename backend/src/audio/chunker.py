import asyncio
import subprocess
import uuid
from typing import List, Tuple, Optional
from loguru import logger

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


class AudioChunker:
    """音频分块处理器，使用 ffmpeg"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.STORAGE_DIR) / "audio_chunks"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_duration = settings.AUDIO_CHUNK_DURATION_MINUTES * 60  # 转换为秒

    async def get_audio_duration(self, file_path: str) -> float:
        """获取音频文件时长（秒）"""
        import asyncio

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]

        def _run_ffprobe():
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
                duration = float(result.stdout.strip())
                return duration
            except subprocess.CalledProcessError as e:
                logger.error(f"ffprobe 错误: {e.stderr}")
                raise Exception(f"无法获取音频时长: {e.stderr}")
            except FileNotFoundError:
                raise Exception("未找到 ffprobe，请安装 ffmpeg")

        return await asyncio.to_thread(_run_ffprobe)

    async def get_audio_size(self, file_path: str) -> int:
        """获取音频文件大小（字节）"""
        return Path(file_path).stat().st_size

    async def chunk_audio(
        self, file_path: str, task_id: Optional[str] = None
    ) -> List[Tuple[str, float, float]]:
        """
        将音频文件分块

        Args:
            file_path: 原音频文件路径
            task_id: 任务 ID（用于生成 chunk 文件名）

        Returns:
            列表: [(chunk_file_path, start_time, end_time), ...]
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        duration = await self.get_audio_duration(file_path)
        logger.info(
            f"音频总时长: {duration:.2f} 秒, 分块时长: {self.chunk_duration} 秒"
        )

        chunks = []
        num_chunks = int(duration / self.chunk_duration) + 1

        for i in range(num_chunks):
            start_time = i * self.chunk_duration
            end_time = min((i + 1) * self.chunk_duration, duration)

            chunk_file = self.storage_dir / f"{task_id}_chunk_{i:04d}.mp3"

            await self._split_audio(
                file_path, str(chunk_file), start_time, end_time - start_time
            )

            chunks.append((str(chunk_file), start_time, end_time))
            logger.info(f"创建分块 {i + 1}/{num_chunks}: {chunk_file}")

        return chunks

    async def _split_audio(
        self, input_file: str, output_file: str, start_time: float, duration: float
    ):
        """使用 ffmpeg 分割音频"""
        import asyncio

        cmd = [
            "ffmpeg",
            "-i",
            input_file,
            "-ss",
            str(start_time),
            "-t",
            str(duration),
            "-c:a",
            "libmp3lame",
            "-ar",
            "16000",
            "-y",
            output_file,
        ]

        def _run_ffmpeg():
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
                return result
            except subprocess.CalledProcessError as e:
                logger.error(f"ffmpeg 错误: {e.stderr}")
                raise Exception(f"音频分块失败: {e.stderr}")

        await asyncio.to_thread(_run_ffmpeg)

    def cleanup_chunks(self, task_id: str):
        """清理任务的分块文件"""
        pattern = f"{task_id}_chunk_*.mp3"
        for chunk_file in self.storage_dir.glob(pattern):
            try:
                chunk_file.unlink()
                logger.info(f"删除分块文件: {chunk_file}")
            except Exception as e:
                logger.error(f"删除分块文件失败 {chunk_file}: {e}")
