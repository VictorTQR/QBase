from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from config import settings

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 创建基类
Base = declarative_base()


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库初始化完成")


async def get_db():
    """获取数据库会话的依赖项"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
