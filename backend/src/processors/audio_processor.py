import time
import uuid
from typing import Any, Optional
from loguru import logger

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from processors.base import FileProcessor
from audio.providers import ASRProvider, SiliconFlowASRProvider
from audio.chunker import AudioChunker
from audio.task_manager import AudioTaskManager
from audio.utils import is_audio_file
from models.audio_schemas import AudioTaskStatus, AudioChunkInfo, AudioTaskInfo


class AudioProcessor(FileProcessor):
    """音频文件处理器"""

    def __init__(
        self, task_manager: AudioTaskManager, chunker: Optional[AudioChunker] = None
    ):
        self.task_manager = task_manager
        self.chunker = chunker or AudioChunker()

    async def process(self, file_path: str, config: Optional[dict] = None) -> dict:
        config = config or {}
        task_id = str(uuid.uuid4())

        # 创建任务记录
        task = await self._create_task(task_id, file_path)

        # 启动后台处理（不阻塞请求）
        import asyncio

        asyncio.create_task(self._process_task(task_id, file_path, config))

        return {
            "task_id": task_id,
            "status": AudioTaskStatus.PENDING,
            "message": "音频转录任务已创建",
        }

    async def _create_task(self, task_id: str, file_path: str) -> AudioTaskInfo:
        logger.debug(f"创建任务: task_id={task_id}, file_path={file_path}")
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            logger.error(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"音频文件不存在: {file_path}")

        total_size = file_path_obj.stat().st_size
        logger.debug(f"文件大小: {total_size} 字节")

        total_duration = await self.chunker.get_audio_duration(file_path)
        logger.debug(f"音频时长: {total_duration} 秒")

        task = AudioTaskInfo(
            task_id=task_id,
            file_path=file_path,
            file_name=file_path_obj.name,
            total_duration=total_duration,
            total_size=total_size,
            status=AudioTaskStatus.PENDING,
            created_at=time.time(),
            updated_at=time.time(),
        )

        await self.task_manager.add_task(task)
        return task

    async def _process_task(self, task_id: str, file_path: str, config: dict):
        try:
            task = await self.task_manager.get_task(task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return

            # 更新状态为分块中
            task.status = AudioTaskStatus.CHUNKING
            task.updated_at = time.time()
            await self.task_manager.update_task(task)

            # 1. 音频分块
            chunks = await self.chunker.chunk_audio(file_path, task_id)

            chunk_infos = []
            for i, (chunk_file, start, end) in enumerate(chunks):
                chunk_info = AudioChunkInfo(
                    chunk_id=f"{task_id}_chunk_{i}",
                    file_path=chunk_file,
                    start_time=start,
                    end_time=end,
                    duration=end - start,
                    status=AudioTaskStatus.PENDING,
                )
                chunk_infos.append(chunk_info)

            task.chunks = chunk_infos
            task.status = AudioTaskStatus.TRANSCRIBING
            task.updated_at = time.time()
            await self.task_manager.update_task(task)

            # 2. 创建 ASR 提供商
            provider = SiliconFlowASRProvider(
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_API_BASE_URL,
                model=config.get("model") if config else None,
            )

            # 3. 逐块转录
            all_transcriptions = []
            for i, chunk_info in enumerate(chunk_infos):
                try:
                    chunk_info.status = AudioTaskStatus.TRANSCRIBING
                    task.updated_at = time.time()
                    await self.task_manager.update_task(task)

                    transcription = await provider.transcribe(
                        chunk_info.file_path, model=config.get("model")
                    )

                    chunk_info.transcription = transcription
                    chunk_info.status = AudioTaskStatus.COMPLETED
                    all_transcriptions.append(
                        (chunk_info.start_time, chunk_info.end_time, transcription)
                    )

                    logger.info(f"分块 {i + 1}/{len(chunk_infos)} 转录完成")

                except Exception as e:
                    chunk_info.status = AudioTaskStatus.FAILED
                    chunk_info.error = str(e)
                    logger.error(f"分块 {i + 1} 转录失败: {e}")

                task.updated_at = time.time()
                await self.task_manager.update_task(task)

            await provider.close()

            # 4. 合并转录结果
            task.status = AudioTaskStatus.MERGING
            task.updated_at = time.time()
            await self.task_manager.update_task(task)

            from audio.utils import merge_transcriptions

            final_transcription = merge_transcriptions(all_transcriptions)
            task.transcription = final_transcription
            task.status = AudioTaskStatus.COMPLETED
            task.updated_at = time.time()
            await self.task_manager.update_task(task)

            # 5. 清理分块文件
            self.chunker.cleanup_chunks(task_id)

            logger.info(
                f"任务 {task_id} 完成，转录文本长度: {len(final_transcription)}"
            )

        except Exception as e:
            logger.error(f"任务 {task_id} 处理失败: {e}")
            task = await self.task_manager.get_task(task_id)
            if task:
                task.status = AudioTaskStatus.FAILED
                task.error = str(e)
                task.updated_at = time.time()
                await self.task_manager.update_task(task)

    def supports(self, file_path: str) -> bool:
        return is_audio_file(file_path)
