from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from src.config import settings

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 创建基类
Base = declarative_base()


async def init_db():
    """初始化数据库，兼容元数据重复注册场景"""
    from sqlalchemy import text
    from src.models.db_models import Base

    def _safe_init(sync_conn):
        """安全初始化：捕获元数据冲突 + 索引冲突"""
        try:
            # 首选：标准幂等创建
            Base.metadata.create_all(sync_conn, checkfirst=True)
        except Exception as e:
            err = str(e).lower()

            # 情况1: 元数据重复注册 -> 跳过（表已定义，无需处理）
            if "already defined for this metadata" in err:
                logger.debug("MetaData already registered, skipping table definition")
                return

            # 情况2: 索引/表已存在 -> 降级逐表处理
            if "already exists" in err:
                logger.debug("Object exists, falling back to per-table creation")
                for table in Base.metadata.sorted_tables:
                    try:
                        table.create(sync_conn, checkfirst=True)
                    except Exception as e2:
                        if "already exists" in str(e2).lower():
                            logger.debug(f"Skip existing: {table.name}")
                        else:
                            raise
            else:
                # 其他未知错误，原样抛出
                raise

    async with engine.begin() as conn:
        await conn.run_sync(_safe_init)
    logger.info("数据库初始化完成")


async def get_db():
    """获取数据库会话的依赖项"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
