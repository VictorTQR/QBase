import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository
from utils.websocket_manager import websocket_manager
from models.audio_schemas import AudioTaskInfo, AudioTaskStatus, AudioChunkInfo


class AudioTaskManager:
    """音频任务管理器（数据库存储）"""

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
            chunk_infos.append(
                AudioChunkInfo(
                    chunk_id=chunk_data.get("chunk_id", ""),
                    file_path=chunk_data.get("file_path", ""),
                    start_time=chunk_data.get("start_time", 0),
                    end_time=chunk_data.get("end_time", 0),
                    duration=chunk_data.get("duration", 0),
                    status=self._map_state_to_status(
                        chunk_data.get("status", "pending")
                    ),
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

    async def add_task(self, task_info: AudioTaskInfo):
        """添加音频任务到数据库"""
        import json
        import time

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
                "file_hash": f"audio_{task_info.task_id}",
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
            return task
        finally:
            await session.close()

    def get_task(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取音频任务（同步包装）"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在事件循环中，创建任务
                task = asyncio.create_task(self._get_task_async(task_id))
                return loop.run_until_complete(task)
            else:
                return loop.run_until_complete(self._get_task_async(task_id))
        except RuntimeError:
            # 如果没有事件循环，创建新的
            import asyncio

            return asyncio.run(self._get_task_async(task_id))

    async def _get_task_async(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取音频任务（异步实现）"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_id(task_id)
            if task and task.file_type == "audio":
                return self._parse_task_to_audio_info(task)
            return None
        finally:
            await session.close()

    def update_task(self, task_info: AudioTaskInfo):
        """更新音频任务（同步包装）"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self._update_task_async(task_info))
                return loop.run_until_complete(task)
            else:
                return loop.run_until_complete(self._update_task_async(task_info))
        except RuntimeError:
            import asyncio

            return asyncio.run(self._update_task_async(task_info))

    async def _update_task_async(self, task_info: AudioTaskInfo):
        """更新音频任务（异步实现）"""
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

    def remove_task(self, task_id: str):
        """删除音频任务（同步包装）"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self._remove_task_async(task_id))
                loop.run_until_complete(task)
            else:
                loop.run_until_complete(self._remove_task_async(task_id))
        except RuntimeError:
            import asyncio

            asyncio.run(self._remove_task_async(task_id))

    async def _remove_task_async(self, task_id: str):
        """删除音频任务（异步实现）"""
        repo, session = await self._get_repo()
        try:
            from sqlalchemy import delete
            from models.db_models import ParseTask

            await session.execute(delete(ParseTask).where(ParseTask.id == task_id))
            await session.commit()
            logger.info(f"删除音频任务: {task_id}")
        finally:
            await session.close()

    def get_all_tasks(self) -> Dict[str, AudioTaskInfo]:
        """获取所有音频任务（同步包装）"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self._get_all_tasks_async())
                return loop.run_until_complete(task)
            else:
                return loop.run_until_complete(self._get_all_tasks_async())
        except RuntimeError:
            import asyncio

            return asyncio.run(self._get_all_tasks_async())

    async def _get_all_tasks_async(self) -> Dict[str, AudioTaskInfo]:
        """获取所有音频任务（异步实现）"""
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
