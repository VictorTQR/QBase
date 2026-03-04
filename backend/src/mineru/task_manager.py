import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from pathlib import Path
from loguru import logger

from config import settings
from mineru.client import mineru_client
from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository
from utils.file_hash import compute_bytes_hash, compute_file_hash
from utils.websocket_manager import websocket_manager


class TaskManager:
    def __init__(self):
        pass

    async def _get_repo(self):
        """获取数据库会话和 repository"""
        session = AsyncSessionLocal()
        return ParseTaskRepository(session), session

    async def check_duplicate(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """检查文件是否已解析（去重检查）"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_hash(file_hash)
            if task and task.state == "done":
                return self._task_to_dict(task)
            return None
        finally:
            await session.close()

    async def create_task(
        self,
        batch_id: str,
        file_name: str,
        file_content: Optional[bytes] = None,
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建解析任务"""
        # 计算文件哈希
        if not file_hash:
            if file_content:
                file_hash = compute_bytes_hash(file_content)
            elif file_path:
                file_hash = await compute_file_hash(file_path)
            else:
                raise ValueError("必须提供 file_content 或 file_path")

        # 检查是否已存在
        existing = await self.check_duplicate(file_hash)
        if existing:
            logger.info(f"文件已解析，返回已有结果: {existing['id']}")
            return existing

        # 计算文件大小
        file_size = None
        if file_content:
            file_size = len(file_content)
        elif file_path:
            file_size = Path(file_path).stat().st_size

        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "batch_id": batch_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "parser_type": "mineru",
            "file_type": "document",
            "state": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        repo, session = await self._get_repo()
        try:
            task = await repo.create(task_data)
            return self._task_to_dict(task)
        finally:
            await session.close()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        repo, session = await self._get_repo()
        try:
            task = await repo.get_by_id(task_id)
            return self._task_to_dict(task) if task else None
        finally:
            await session.close()

    async def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """更新任务"""
        repo, session = await self._get_repo()
        try:
            task = await repo.update(task_id, kwargs)
            if "state" in kwargs:
                if task:
                    await websocket_manager.broadcast_task_update(
                        "mineru",
                        {
                            "type": "task_update",
                            "task_id": task_id,
                            "task_type": "mineru",
                            "state": kwargs["state"],
                            "data": self._task_to_dict(task),
                        },
                    )
            return self._task_to_dict(task) if task else None
        finally:
            await session.close()

    async def list_tasks(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出所有任务"""
        repo, session = await self._get_repo()
        try:
            tasks = await repo.list_all(limit, offset)
            return [self._task_to_dict(task) for task in tasks]
        finally:
            await session.close()

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        repo, session = await self._get_repo()
        try:
            return await repo.get_stats()
        finally:
            await session.close()

    async def clear_completed(self) -> int:
        """清除已完成的任务"""
        repo, session = await self._get_repo()
        try:
            return await repo.delete_by_states(["done"])
        finally:
            await session.close()

    async def clear_all(self) -> int:
        """清空所有任务"""
        repo, session = await self._get_repo()
        try:
            return await repo.delete_all()
        finally:
            await session.close()

    async def batch_parse_pending(self, background_tasks) -> int:
        """批量解析待处理文件"""
        repo, session = await self._get_repo()
        try:
            pending_tasks = await repo.list_by_state("pending", limit=100)
            count = 0
            for task in pending_tasks:
                task_dict = self._task_to_dict(task)
                background_tasks.add_task(self.poll_task_status, task_dict["id"])
                count += 1
            logger.info(f"批量启动了 {count} 个待解析任务")
            return count
        finally:
            await session.close()

    async def retry_failed(self, background_tasks) -> int:
        """重试失败的任务"""
        repo, session = await self._get_repo()
        try:
            failed_tasks = await repo.list_by_state("failed", limit=100)
            count = 0
            for task in failed_tasks:
                # 重置任务状态为 pending
                await repo.update(
                    task.id,
                    {
                        "state": "pending",
                        "error_msg": None,
                        "updated_at": datetime.now().isoformat(),
                    },
                )
                task_dict = self._task_to_dict(task)
                background_tasks.add_task(self.poll_task_status, task_dict["id"])
                count += 1
            logger.info(f"重试了 {count} 个失败任务")
            return count
        finally:
            await session.close()

    def _task_to_dict(self, task) -> Dict[str, Any]:
        """将数据库模型转换为字典"""
        return {
            "id": task.id,
            "batch_id": task.batch_id,
            "file_name": task.file_name,
            "file_path": task.file_path,
            "file_hash": task.file_hash,
            "state": task.state,
            "error_msg": task.error_msg,
            "markdown_content": task.markdown_content,
            "result_file_path": task.result_file_path,
            "result_file_format": task.result_file_format,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "file_type": getattr(task, "file_type", "document"),
            "metadata": getattr(task, "metadata", None),
        }

    async def poll_task_status(self, task_id: str) -> None:
        """轮询任务状态（保持原有逻辑）"""
        task = await self.get_task(task_id)
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        await self.update_task(task_id, state="running")

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
                    await self.update_task(task_id, state="done")
                    logger.info(f"任务 {task_id} 完成")
                    return
                elif state == "failed":
                    err_msg = file_result.get("err_msg", "任务执行失败")
                    await self.update_task(task_id, state="failed", error_msg=err_msg)
                    logger.error(f"任务 {task_id} 失败: {err_msg}")
                    return
                elif state == "running" and file_result.get("extract_progress"):
                    progress = file_result["extract_progress"]
                    logger.info(
                        f"解析进度: {progress.get('extracted_pages', 0)}/{progress.get('total_pages', 0)} 页"
                    )

            except Exception as e:
                logger.error(f"轮询任务 {task_id} 出错: {str(e)}")
                await self.update_task(task_id, state="failed", error_msg=str(e))
                return

            await asyncio.sleep(settings.TASK_POLL_INTERVAL)

        await self.update_task(task_id, state="failed", error_msg="任务超时")
        logger.error(f"任务 {task_id} 超时")


task_manager = TaskManager()
