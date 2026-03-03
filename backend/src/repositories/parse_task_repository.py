from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.db_models import ParseTask


class ParseTaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, task_data: Dict[str, Any]) -> ParseTask:
        """创建新的解析任务"""
        task = ParseTask(**task_data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        logger.info(f"创建解析任务: {task.id}")
        return task

    async def get_by_id(self, task_id: str) -> Optional[ParseTask]:
        """通过 ID 获取任务"""
        result = await self.db.execute(select(ParseTask).where(ParseTask.id == task_id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, file_hash: str) -> Optional[ParseTask]:
        """通过文件哈希获取任务（用于去重检查）"""
        result = await self.db.execute(
            select(ParseTask).where(ParseTask.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    async def update(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Optional[ParseTask]:
        """更新任务"""
        task = await self.get_by_id(task_id)
        if not task:
            return None

        updates["updated_at"] = datetime.now().isoformat()
        for key, value in updates.items():
            setattr(task, key, value)

        await self.db.commit()
        await self.db.refresh(task)
        logger.info(f"更新任务 {task_id}: {updates.keys()}")
        return task

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ParseTask]:
        """列出所有任务（分页）"""
        result = await self.db.execute(
            select(ParseTask)
            .order_by(desc(ParseTask.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_state(self, state: str, limit: int = 100) -> List[ParseTask]:
        """按状态列出任务"""
        result = await self.db.execute(
            select(ParseTask)
            .where(ParseTask.state == state)
            .order_by(desc(ParseTask.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self) -> Dict[str, Any]:
        """获取解析统计"""
        # 总数
        total_result = await self.db.execute(select(func.count(ParseTask.id)))
        total = total_result.scalar()

        # 按状态统计
        states = ["pending", "running", "done", "failed"]
        stats = {"total": total or 0}

        for state in states:
            result = await self.db.execute(
                select(func.count(ParseTask.id)).where(ParseTask.state == state)
            )
            stats[state] = result.scalar() or 0

        return stats
