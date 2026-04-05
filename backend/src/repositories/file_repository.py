from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import DBFile
from loguru import logger


class FileRepository:
    """文件数据访问层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, file_data: dict) -> DBFile:
        """创建文件记录"""
        db_file = DBFile(**file_data)
        self.session.add(db_file)
        await self.session.commit()
        await self.session.refresh(db_file)
        logger.debug(f"创建文件记录: {db_file.hash}")
        return db_file

    async def get_by_hash(self, file_hash: str) -> Optional[DBFile]:
        """通过哈希获取文件"""
        result = await self.session.execute(
            select(DBFile).where(DBFile.hash == file_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_path(self, rel_path: str) -> Optional[DBFile]:
        """通过相对路径获取文件"""
        result = await self.session.execute(
            select(DBFile).where(DBFile.rel_path == rel_path)
        )
        return result.scalar_one_or_none()

    async def update(self, file_hash: str, update_data: dict) -> Optional[DBFile]:
        """更新文件记录"""
        stmt = update(DBFile).where(DBFile.hash == file_hash).values(**update_data)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_hash(file_hash)

    async def list_all(self, status: Optional[str] = None) -> List[DBFile]:
        """列出所有文件"""
        query = select(DBFile)
        if status:
            query = query.where(DBFile.status == status)
        result = await self.session.execute(query.order_by(DBFile.updated_at.desc()))
        return list(result.scalars().all())

    async def delete(self, file_hash: str) -> bool:
        """删除文件记录"""
        stmt = delete(DBFile).where(DBFile.hash == file_hash)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
