"""论文数据库模块"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    create_engine,
    select,
    func,
    desc,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    Session,
)
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger
import json

# 创建独立的数据库 Base
Base = declarative_base()


class DBPaper(Base):
    """已保存的论文"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    keyword = Column(String, nullable=False, index=True)
    search_sort_type = Column(String, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship("DBPaper", back_populates="search_keywords")

    __table_args__ = (
        UniqueConstraint(
            "paper_id", "keyword", "search_sort_type", name="_paper_keyword_sort_uc"
        ),
    )


class PaperDatabase:
    """论文数据库操作类"""

    def __init__(self, db_path: str = "./papers.db"):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._init_db()
        logger.info(f"PaperDatabase 初始化完成 (数据库: {db_path})")

    def _init_db(self):
        """初始化数据库表"""
        Base.metadata.create_all(self.engine)
        logger.info("论文数据库表初始化完成")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return Session(self.engine)

    def save_paper(
        self, paper_data: Dict[str, Any], keyword: str, sort_type: str
    ) -> Optional[int]:
        """
        保存论文到数据库

        Args:
            paper_data: 论文数据字典
            keyword: 搜索关键词
            sort_type: 排序类型

        Returns:
            论文 ID，如果已存在则返回 None
        """
        with self.get_session() as session:
            try:
                # 检查论文是否已存在
                existing = (
                    session.query(DBPaper)
                    .filter(DBPaper.entry_id == paper_data["entry_id"])
                    .first()
                )
                if existing:
                    logger.debug(f"论文已存在: {paper_data['title']}")
                    return None

                # 创建论文记录
                db_paper = DBPaper(**paper_data)
                session.add(db_paper)
                session.flush()  # 获取 ID

                # 创建关键词关联
                keyword_assoc = DBPaperKeyword(
                    paper_id=db_paper.id,
                    keyword=keyword,
                    search_sort_type=sort_type,
                )
                session.add(keyword_assoc)

                session.commit()
                logger.info(f"保存论文: {paper_data['title']}")
                return db_paper.id

            except Exception as e:
                session.rollback()
                logger.error(f"保存论文时出错: {e}")
                raise

    def get_paper_by_entry_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        通过 entry_id 获取论文

        Args:
            entry_id: 论文 entry_id

        Returns:
            论文字典，未找到则返回 None
        """
        with self.get_session() as session:
            try:
                paper = (
                    session.query(DBPaper)
                    .filter(DBPaper.entry_id == entry_id)
                    .first()
                )
                if not paper:
                    return None

                return {
                    "id": paper.id,
                    "entry_id": paper.entry_id,
                    "title": paper.title,
                    "authors": json.loads(paper.authors),
                    "summary": paper.summary,
                    "published": paper.published.isoformat(),
                    "updated": paper.updated.isoformat(),
                    "pdf_url": paper.pdf_url,
                    "primary_category": paper.primary_category,
                    "categories": json.loads(paper.categories),
                    "links": json.loads(paper.links),
                    "created_at": paper.created_at.isoformat(),
                    "updated_at": paper.updated_at.isoformat(),
                }
            except Exception as e:
                logger.error(f"获取论文时出错: {e}")
                raise

    def list_papers(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出所有论文（分页）

        Args:
            limit: 每页数量
            offset: 偏移量

        Returns:
            论文列表
        """
        with self.get_session() as session:
            try:
                papers = (
                    session.query(DBPaper)
                    .order_by(desc(DBPaper.created_at))
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                return [
                    {
                        "id": p.id,
                        "entry_id": p.entry_id,
                        "title": p.title,
                        "authors": json.loads(p.authors),
                        "summary": p.summary,
                        "published": p.published.isoformat(),
                        "updated": p.updated.isoformat(),
                        "pdf_url": p.pdf_url,
                        "primary_category": p.primary_category,
                        "categories": json.loads(p.categories),
                        "links": json.loads(p.links),
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat(),
                    }
                    for p in papers
                ]
            except Exception as e:
                logger.error(f"列出论文时出错: {e}")
                raise

    def get_stats(self) -> Dict[str, int]:
        """
        获取论文统计信息

        Returns:
            统计信息字典
        """
        with self.get_session() as session:
            try:
                # 总论文数
                total_papers = session.query(func.count(DBPaper.id)).scalar() or 0

                # 总关键词数
                total_keywords = (
                    session.query(func.count(DBPaperKeyword.id)).scalar() or 0
                )

                # 最近 7 天的论文数
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                recent_papers = (
                    session.query(func.count(DBPaper.id))
                    .filter(DBPaper.created_at >= seven_days_ago)
                    .scalar()
                    or 0
                )

                return {
                    "total_papers": total_papers,
                    "total_keywords": total_keywords,
                    "recent_papers": recent_papers,
                }
            except Exception as e:
                logger.error(f"获取统计信息时出错: {e}")
                raise

    def delete_paper(self, entry_id: str) -> bool:
        """
        删除论文

        Args:
            entry_id: 论文 entry_id

        Returns:
            是否成功删除
        """
        with self.get_session() as session:
            try:
                paper = (
                    session.query(DBPaper)
                    .filter(DBPaper.entry_id == entry_id)
                    .first()
                )
                if not paper:
                    return False

                session.delete(paper)
                session.commit()
                logger.info(f"删除论文: {paper.title}")
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"删除论文时出错: {e}")
                raise


# 导出单例
paper_database = PaperDatabase()
