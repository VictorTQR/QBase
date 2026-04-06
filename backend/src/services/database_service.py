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
        """初始化工作区数据库，创建所有表"""
        from src.models.db_models import ParseTask, DBFile, DBDerivative, DBTask

        engine = cls.get_engine(workspace_path)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Workspace database initialized for: {workspace_path}")

    @classmethod
    async def get_session(cls, workspace_path: str):
        """获取工作区的数据库会话（上下文管理器）"""
        session_factory = cls.get_session_factory(workspace_path)
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
