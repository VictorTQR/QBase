from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import DBDerivative
from loguru import logger


class DerivativeRepository:
    """派生数据访问层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, derivative_data: dict) -> DBDerivative:
        """创建派生数据记录"""
        db_derivative = DBDerivative(**derivative_data)
        self.session.add(db_derivative)
        await self.session.commit()
        await self.session.refresh(db_derivative)
        logger.debug(f"创建派生数据: {db_derivative.file_hash} - {db_derivative.type}")
        return db_derivative

    async def get_by_file_and_type(
        self, file_hash: str, derivative_type: str
    ) -> Optional[DBDerivative]:
        """获取指定文件的指定类型派生数据"""
        result = await self.session.execute(
            select(DBDerivative)
            .where(DBDerivative.file_hash == file_hash)
            .where(DBDerivative.type == derivative_type)
            .order_by(DBDerivative.version.desc())
        )
        return result.scalar_one_or_none()

    async def list_by_file(self, file_hash: str) -> List[DBDerivative]:
        """列出文件的所有派生数据"""
        result = await self.session.execute(
            select(DBDerivative).where(DBDerivative.file_hash == file_hash)
        )
        return list(result.scalars().all())

    async def update_status(
        self, derivative_id: int, status: str
    ) -> Optional[DBDerivative]:
        """更新状态"""
        stmt = (
            update(DBDerivative)
            .where(DBDerivative.id == derivative_id)
            .values(status=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        result = await self.session.execute(
            select(DBDerivative).where(DBDerivative.id == derivative_id)
        )
        return result.scalar_one_or_none()
