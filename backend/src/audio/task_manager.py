import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import threading
from typing import Dict, Optional
from loguru import logger

from models.audio_schemas import AudioTaskInfo


class AudioTaskManager:
    """音频任务管理器（内存存储，简单实现）"""

    _instance: Optional["AudioTaskManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, AudioTaskInfo] = {}
        return cls._instance

    def __init__(self):
        pass  # 单例，只在 __new__ 中初始化

    def add_task(self, task: AudioTaskInfo):
        """添加任务"""
        with self._lock:
            self._tasks[task.task_id] = task
            logger.info(f"添加音频任务: {task.task_id}")

    def get_task(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取任务"""
        return self._tasks.get(task_id)

    def update_task(self, task: AudioTaskInfo):
        """更新任务"""
        with self._lock:
            self._tasks[task.task_id] = task

    def remove_task(self, task_id: str):
        """移除任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"移除音频任务: {task_id}")

    def get_all_tasks(self) -> Dict[str, AudioTaskInfo]:
        """获取所有任务"""
        with self._lock:
            return dict(self._tasks)


# 全局单例实例
audio_task_manager = AudioTaskManager()
