from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger

from src.config import settings
from src.database import Base


class WorkspaceDatabaseService:
    """工作区数据库服务 - 管理每个工作区的 metadata.db"""

    _engines = {}  # workspace_path -> engine
    _session_factories = {}  # workspace_path -> session_factory

    @classmethod
    def get_engine(cls, workspace_path: str):
        """获取工作区的数据库引擎"""
        if workspace_path in cls._engines:
            return cls._engines[workspace_path]

        db_path = Path(workspace_path) / ".qbase" / settings.WORKSPACE_DATABASE_NAME
        db_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_async_engine(db_url, echo=False, future=True)
        cls._engines[workspace_path] = engine

        logger.info(f"Workspace database engine created for: {workspace_path}")
        return engine

    @classmethod
    def get_session_factory(cls, workspace_path: str):
        """获取工作区的会话工厂"""
        if workspace_path in cls._session_factories:
            return cls._session_factories[workspace_path]

        engine = cls.get_engine(workspace_path)
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        cls._session_factories[workspace_path] = session_factory

        return session_factory

    @classmethod
    async def init_workspace_db(cls, workspace_path: str):
        """初始化工作区数据库，兼容元数据重复注册场景"""
        from sqlalchemy import text
        from src.models.db_models import Base

        engine = cls.get_engine(workspace_path)

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

        logger.info(f"Workspace database ready: {workspace_path}")

    @classmethod
    async def get_session(cls, workspace_path: str):
        """获取工作区的数据库会话（上下文管理器）"""
        session_factory = cls.get_session_factory(workspace_path)
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
