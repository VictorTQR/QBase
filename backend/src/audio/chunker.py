import asyncio
import subprocess
import uuid
from typing import List, Tuple, Optional
from loguru import logger
from pathlib import Path

from config import settings


class AudioChunker:
    """音频分块处理器，使用 ffmpeg"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.STORAGE_DIR) / "audio_chunks"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def chunk_audio(
        self, audio_path: str, chunk_duration_minutes: int = None
    ) -> Tuple[List[dict], float]:
        """
        将音频文件分块

        Args:
            audio_path: 音频文件路径
            chunk_duration_minutes: 每个分块的时长（分钟），默认使用配置

        Returns:
            (分块列表, 总时长秒数)
        """
        from pathlib import Path

        chunk_duration = (
            chunk_duration_minutes or settings.AUDIO_CHUNK_DURATION_MINUTES
        )
        chunk_duration_seconds = chunk_duration * 60

        # 获取音频总时长
        total_duration = await self._get_audio_duration(audio_path)
        if total_duration is None:
            raise ValueError(f"无法获取音频时长: {audio_path}")

        logger.info(f"音频总时长: {total_duration:.2f}秒, 分块时长: {chunk_duration}分钟")

        # 如果音频短于分块时长，不需要分块
        if total_duration <= chunk_duration_seconds:
            logger.info("音频时长较短，无需分块")
            return (
                [
                    {
                        "chunk_id": str(uuid.uuid4()),
                        "file_path": audio_path,
                        "start_time": 0,
                        "end_time": total_duration,
                        "duration": total_duration,
                    }
                ],
                total_duration,
            )

        # 创建分块
        chunks = []
        chunk_count = int(total_duration // chunk_duration_seconds) + 1
        base_name = Path(audio_path).stem

        for i in range(chunk_count):
            start_time = i * chunk_duration_seconds
            end_time = min((i + 1) * chunk_duration_seconds, total_duration)
            duration = end_time - start_time

            if duration <= 0:
                break

            chunk_id = str(uuid.uuid4())
            chunk_filename = f"{base_name}_chunk_{i:04d}_{chunk_id}.wav"
            chunk_path = self.storage_dir / chunk_filename

            # 使用 ffmpeg 提取分块
            await self._extract_chunk(audio_path, chunk_path, start_time, duration)

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "file_path": str(chunk_path),
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                }
            )

            logger.info(f"创建音频分块 {i+1}/{chunk_count}: {chunk_path}")

        return chunks, total_duration

    async def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        """获取音频文件时长（秒）"""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"ffprobe 失败: {stderr.decode()}")
                return None

            return float(stdout.decode().strip())
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return None

    async def _extract_chunk(
        self, audio_path: str, output_path: Path, start_time: float, duration: float
    ):
        """使用 ffmpeg 提取音频分块"""
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖输出文件
            "-i",
            audio_path,
            "-ss",
            str(start_time),
            "-t",
            str(duration),
            "-ar",
            "16000",  # 采样率 16kHz
            "-ac",
            "1",  # 单声道
            "-c:a",
            "pcm_s16le",  # 16位 PCM
            str(output_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"ffmpeg 分块失败: {error_msg}")
            raise RuntimeError(f"音频分块失败: {error_msg}")

    def cleanup_chunks(self, chunks: List[dict]):
        """清理临时分块文件"""
        from pathlib import Path

        for chunk in chunks:
            chunk_path = Path(chunk["file_path"])
            # 只删除存储在 chunks 目录中的临时文件
            if self.storage_dir in chunk_path.parents:
                try:
                    chunk_path.unlink(missing_ok=True)
                    logger.debug(f"删除临时分块文件: {chunk_path}")
                except Exception as e:
                    logger.warning(f"删除分块文件失败: {chunk_path}, {e}")
