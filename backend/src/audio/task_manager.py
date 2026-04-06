import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from ..database import AsyncSessionLocal
from ..repositories.parse_task_repository import ParseTaskRepository
from ..utils.websocket_manager import websocket_manager
from ..models.audio_schemas import AudioTaskInfo, AudioTaskStatus, AudioChunkInfo


class AudioTaskManager:
    """音频任务管理器（数据库存储，纯异步）"""

    _instance: Optional["AudioTaskManager"] = None
    _lock = None

    def __new__(cls):
        import threading

        if cls._instance is None:
            cls._lock = threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    async def _get_repo(self):
        """获取数据库会话和 repository"""
        session = AsyncSessionLocal()
        return ParseTaskRepository(session), session

    def _map_status_to_state(self, status: AudioTaskStatus) -> str:
        """将音频状态映射为统一状态"""
        status_map = {
            AudioTaskStatus.PENDING: "pending",
            AudioTaskStatus.PROCESSING: "running",
            AudioTaskStatus.CHUNKING: "running",
            AudioTaskStatus.TRANSCRIBING: "running",
            AudioTaskStatus.MERGING: "running",
            AudioTaskStatus.COMPLETED: "done",
            AudioTaskStatus.FAILED: "failed",
        }
        return status_map.get(status, "pending")

    def _map_state_to_status(self, state: str) -> AudioTaskStatus:
        """将统一状态映射为音频状态"""
        state_map = {
            "pending": AudioTaskStatus.PENDING,
            "running": AudioTaskStatus.PROCESSING,
            "done": AudioTaskStatus.COMPLETED,
            "failed": AudioTaskStatus.FAILED,
        }
        return state_map.get(state, AudioTaskStatus.PENDING)

    def _parse_task_to_audio_info(self, task) -> AudioTaskInfo:
        """将数据库 ParseTask 转换为 AudioTaskInfo"""
        import json

        metadata = {}
        if task.task_metadata:
            try:
                metadata = json.loads(task.task_metadata)
            except:
                pass

        status = self._map_state_to_status(task.state)
        chunks = metadata.get("chunks", [])
        chunk_infos = []
        for chunk_data in chunks:
            chunk_status_str = chunk_data.get("status", "pending")
            # 将字符串状态转换为 AudioTaskStatus 枚举
            from ..models.audio_schemas import AudioTaskStatus

            chunk_status = AudioTaskStatus.PENDING
            for status in AudioTaskStatus:
                if status.value == chunk_status_str:
                    chunk_status = status
                    break

            chunk_infos.append(
                AudioChunkInfo(
                    chunk_id=chunk_data.get("chunk_id", ""),
                    file_path=chunk_data.get("file_path", ""),
                    start_time=chunk_data.get("start_time", 0),
                    end_time=chunk_data.get("end_time", 0),
                    duration=chunk_data.get("duration", 0),
                    status=chunk_status,
                    transcription=chunk_data.get("transcription"),
                    error=chunk_data.get("error"),
                )
            )

        return AudioTaskInfo(
            task_id=task.id,
            file_path=task.file_path or "",
            file_name=task.file_name,
            total_duration=metadata.get("total_duration", 0),
            total_size=task.file_size or 0,
            status=status,
            chunks=chunk_infos,
            transcription=task.markdown_content,
            error=task.error_msg,
            created_at=metadata.get("created_at_timestamp", 0),
            updated_at=metadata.get("updated_at_timestamp", 0),
        )

    async def add_task(self, task_info: AudioTaskInfo, file_hash: Optional[str] = None):
        """添加音频任务到数据库"""
        import json
        import time

        repo, session = await self._get_repo()
        try:
            # 去重检查
            if file_hash:
                existing = await repo.get_by_hash(file_hash)
                if existing and existing.state == "done":
                    logger.info(f"文件已解析，返回已有结果: {existing.id}")
                    # 将 ParseTask 转换为 AudioTaskInfo 返回
                    return self._parse_task_to_audio_info(existing)

            metadata = {
                "total_duration": task_info.total_duration,
                "chunk_count": len(task_info.chunks),
                "chunks": [],
                "created_at_timestamp": task_info.created_at,
                "updated_at_timestamp": task_info.updated_at,
            }

            for chunk in task_info.chunks:
                metadata["chunks"].append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "file_path": chunk.file_path,
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time,
                        "duration": chunk.duration,
                        "status": chunk.status.value,
                        "transcription": chunk.transcription,
                        "error": chunk.error,
                    }
                )

            task_data = {
                "id": task_info.task_id,
                "batch_id": f"audio_{int(time.time())}",
                "file_name": task_info.file_name,
                "file_path": task_info.file_path,
                "file_hash": file_hash or f"audio_{task_info.task_id}",
                "file_size": task_info.total_size,
                "parser_type": "siliconflow_asr",
                "file_type": "audio",
                "state": self._map_status_to_state(task_info.status),
                "error_msg": task_info.error,
                "markdown_content": task_info.transcription,
                "task_metadata": json.dumps(metadata, ensure_ascii=False),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            task = await repo.create(task_data)
            logger.info(f"添加音频任务到数据库: {task.id}")
            # 将新创建的 ParseTask 转换为 AudioTaskInfo 返回
            return self._parse_task_to_audio_info(task)
        finally:
            await session.close()

    async def get_task(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取音频任务"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_id(task_id)
            if task and task.file_type == "audio":
                return self._parse_task_to_audio_info(task)
            return None
        finally:
            await session.close()

    async def update_task(self, task_info: AudioTaskInfo):
        """更新音频任务"""
        import json

        repo, session = await self._get_repo()
        try:
            metadata = {
                "total_duration": task_info.total_duration,
                "chunk_count": len(task_info.chunks),
                "chunks": [],
                "created_at_timestamp": task_info.created_at,
                "updated_at_timestamp": task_info.updated_at,
            }

            for chunk in task_info.chunks:
                metadata["chunks"].append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "file_path": chunk.file_path,
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time,
                        "duration": chunk.duration,
                        "status": chunk.status.value
                        if hasattr(chunk.status, "value")
                        else str(chunk.status),
                        "transcription": chunk.transcription,
                        "error": chunk.error,
                    }
                )

            updates = {
                "state": self._map_status_to_state(task_info.status),
                "error_msg": task_info.error,
                "markdown_content": task_info.transcription,
                "task_metadata": json.dumps(metadata, ensure_ascii=False),
            }

            task = await repo.update(task_info.task_id, updates)

            # WebSocket 广播
            try:
                asyncio.create_task(
                    websocket_manager.broadcast_task_update(
                        "audio",
                        {
                            "type": "task_update",
                            "task_id": task_info.task_id,
                            "task_type": "audio",
                            "state": self._map_status_to_state(task_info.status),
                            "data": {
                                "task_id": task_info.task_id,
                                "status": task_info.status.value
                                if hasattr(task_info.status, "value")
                                else str(task_info.status),
                                "file_name": task_info.file_name,
                            },
                        },
                    )
                )
            except Exception as e:
                logger.error(f"Failed to broadcast audio task update: {e}")

            return task
        finally:
            await session.close()

    async def remove_task(self, task_id: str):
        """删除音频任务"""
        repo, session = await self._get_repo()
        try:
            from sqlalchemy import delete
            from ..models.db_models import ParseTask

            await session.execute(delete(ParseTask).where(ParseTask.id == task_id))
            await session.commit()
            logger.info(f"删除音频任务: {task_id}")
        finally:
            await session.close()

    async def get_all_tasks(self) -> Dict[str, AudioTaskInfo]:
        """获取所有音频任务"""
        repo, session = await self._get_repo()
        try:
            tasks = await repo.list_by_type("audio", limit=1000)
            result = {}
            for task in tasks:
                result[task.id] = self._parse_task_to_audio_info(task)
            return result
        finally:
            await session.close()


# 全局单例实例
audio_task_manager = AudioTaskManager()
