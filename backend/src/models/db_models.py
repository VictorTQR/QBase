from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
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
