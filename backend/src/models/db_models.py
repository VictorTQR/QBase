from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base


class ParseTask(Base):
    __tablename__ = "parse_tasks"

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


# 论文相关表
class DBPaper(Base):
    """已保存的论文"""

    __tablename__ = "papers"

    id = Column(Integer, primary_key=True)
    entry_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, unique=True, nullable=False)
    authors = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    published = Column(DateTime, nullable=False)
    updated = Column(DateTime, nullable=False)
    pdf_url = Column(String, nullable=False)
    primary_category = Column(String, nullable=False)
    categories = Column(String, nullable=False)
    links = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    search_keywords = relationship(
        "DBPaperKeyword", back_populates="paper", cascade="all, delete-orphan"
    )


class DBPaperKeyword(Base):
    """论文搜索关键词关联"""

    __tablename__ = "paper_keywords"

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    keyword = Column(String, nullable=False)
    search_sort_type = Column(String, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship("DBPaper", back_populates="search_keywords")

    __table_args__ = (
        UniqueConstraint(
            "paper_id", "keyword", "search_sort_type", name="_paper_keyword_sort_uc"
        ),
    )


# ============================================
# 新架构表 (v1.2+)
# ============================================


class DBFile(Base):
    """文件索引表 - 基于内容哈希的文件追踪"""

    __tablename__ = "files"

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
