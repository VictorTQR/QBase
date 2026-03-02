import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from loguru import logger

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from mineru.client import mineru_client


class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def create_task(self, batch_id: str, file_name: str) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "state": "pending",
            "batch_id": batch_id,
            "file_name": file_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error_msg": None,
        }
        self.tasks[task_id] = task
        logger.info(f"创建任务: {task_id}")
        return task

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        if task_id not in self.tasks:
            return None
        task = self.tasks[task_id]
        task.update(kwargs)
        task["updated_at"] = datetime.now().isoformat()
        self.tasks[task_id] = task
        logger.info(f"更新任务 {task_id}: {kwargs}")
        return task

    def list_tasks(self) -> List[Dict[str, Any]]:
        return list(self.tasks.values())

    async def poll_task_status(self, task_id: str) -> None:
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        self.update_task(task_id, state="running")

        for attempt in range(settings.MAX_POLL_ATTEMPTS):
            try:
                result = await mineru_client.batch_query_results(task["batch_id"])

                if "extract_result" not in result or len(result["extract_result"]) == 0:
                    await asyncio.sleep(settings.TASK_POLL_INTERVAL)
                    continue

                file_result = result["extract_result"][0]
                state = file_result.get("state")

                logger.info(f"任务 {task_id} 状态: {state}")

                if state == "done":
                    self.update_task(task_id, state="done", result=file_result)
                    logger.info(f"任务 {task_id} 完成")
                    return
                elif state == "failed":
                    err_msg = file_result.get("err_msg", "任务执行失败")
                    self.update_task(task_id, state="failed", error_msg=err_msg)
                    logger.error(f"任务 {task_id} 失败: {err_msg}")
                    return
                elif state == "running" and file_result.get("extract_progress"):
                    progress = file_result["extract_progress"]
                    logger.info(
                        f"解析进度: {progress.get('extracted_pages', 0)}/{progress.get('total_pages', 0)} 页"
                    )

            except Exception as e:
                logger.error(f"轮询任务 {task_id} 出错: {str(e)}")
                self.update_task(task_id, state="failed", error_msg=str(e))
                return

            await asyncio.sleep(settings.TASK_POLL_INTERVAL)

        self.update_task(task_id, state="failed", error_msg="任务超时")
        logger.error(f"任务 {task_id} 超时")


task_manager = TaskManager()
