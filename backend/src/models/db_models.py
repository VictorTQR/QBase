from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    ForeignKey,
)
from src.database import Base


class ParseTask(Base):
    __tablename__ = "parse_tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    batch_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    file_size = Column(Integer, nullable=True)
    parser_type = Column(String, nullable=False, default="mineru", index=True)
    file_type = Column(String, nullable=False, default="document", index=True)
    state = Column(String, nullable=False, index=True)
    error_msg = Column(Text, nullable=True)
    # DEPRECATED: 使用 .qbase/generated/{hash}/raw_text.md 替代
    markdown_content = Column(Text, nullable=True)
    task_metadata = Column(Text, nullable=True)
    result_file_path = Column(String, nullable=True)
    result_file_format = Column(String, nullable=True, default="zip")
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


# ============================================
# 新架构表 (v1.2+)
# ============================================


class DBFile(Base):
    """文件索引表 - 基于内容哈希的文件追踪"""

    __tablename__ = "files"
    __table_args__ = {"extend_existing": True}

    hash = Column(String(16), primary_key=True, index=True, comment="SHA-256 前16位")
    rel_path = Column(
        String, unique=True, nullable=False, index=True, comment="相对工作区路径"
    )
    file_type = Column(
        String(32), nullable=True, comment="文件类型: md | pdf | audio | video"
    )
    size = Column(Integer, nullable=True, comment="文件大小(字节)")
    mtime = Column(Integer, nullable=True, comment="最后修改时间戳")
    status = Column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
        comment="状态: pending | processing | ready | error | missing | orphan",
    )
    created_at = Column(Integer, nullable=True, comment="创建时间戳")
    updated_at = Column(Integer, nullable=True, comment="更新时间戳")


class DBDerivative(Base):
    """派生数据表 - AI 生成内容的元数据"""

    __tablename__ = "derivatives"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(
        String(16),
        ForeignKey("files.hash", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(
        String(32),
        nullable=False,
        index=True,
        comment="类型: raw_text | transcript | notes | flashcards | mindmap | analysis",
    )
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    model_used = Column(String(255), nullable=True, comment="使用的模型")
    status = Column(
        String(32),
        nullable=False,
        default="ready",
        index=True,
        comment="状态: ready | outdated | error",
    )
    created_at = Column(Integer, nullable=True, comment="创建时间戳")


class DBTask(Base):
    """任务队列表"""

    __tablename__ = "tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(16), ForeignKey("files.hash"), nullable=True, index=True)
    task_type = Column(
        String(32),
        nullable=False,
        index=True,
        comment="任务类型: parse | embed | generate | sync",
    )
    status = Column(
        String(32),
        nullable=False,
        index=True,
        comment="状态: queued | running | success | failed",
    )
    progress = Column(Integer, nullable=False, default=0, comment="进度 0-100")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(Integer, nullable=True, comment="创建时间戳")
    started_at = Column(Integer, nullable=True, comment="开始时间戳")
    completed_at = Column(Integer, nullable=True, comment="完成时间戳")
