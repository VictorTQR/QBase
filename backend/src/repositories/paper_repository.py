from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import DBPaperV2, DBPaperKeywordV2
from loguru import logger
import json
import time


class PaperRepository:
    """论文数据访问层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, paper_data: Dict[str, Any], keyword: str, sort_type: str
    ) -> Optional[Dict[str, Any]]:
        try:
            existing = await self.get_by_entry_id(paper_data["entry_id"])
            if existing:
                logger.debug(f"论文已存在: {paper_data['title']}")
                return None

            now = int(time.time())
            db_paper = DBPaperV2(
                entry_id=paper_data["entry_id"],
                title=paper_data["title"],
                authors=json.dumps(paper_data["authors"], ensure_ascii=False),
                summary=paper_data["summary"],
                published=paper_data.get("published", ""),
                updated=paper_data.get("updated", ""),
                pdf_url=paper_data["pdf_url"],
                primary_category=paper_data["primary_category"],
                categories=json.dumps(
                    paper_data.get("categories", []), ensure_ascii=False
                ),
                links=json.dumps(paper_data.get("links", []), ensure_ascii=False),
                created_at=now,
                updated_at=now,
            )
            self.session.add(db_paper)
            await self.session.flush()

            keyword_assoc = DBPaperKeywordV2(
                paper_id=db_paper.id,
                keyword=keyword,
                search_sort_type=sort_type,
                scraped_at=now,
            )
            self.session.add(keyword_assoc)
            await self.session.commit()
            await self.session.refresh(db_paper)
            logger.info(f"保存论文: {paper_data['title']}")
            return self._to_dict(db_paper)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"保存论文时出错: {e}")
            raise

    async def get_by_entry_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        result = await self.session.execute(
            select(DBPaperV2).where(DBPaperV2.entry_id == entry_id)
        )
        paper = result.scalar_one_or_none()
        return self._to_dict(paper) if paper else None

    async def list_papers(
        self, limit: int = 100, offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        count_result = await self.session.execute(select(func.count(DBPaperV2.id)))
        total = count_result.scalar() or 0

        result = await self.session.execute(
            select(DBPaperV2)
            .order_by(desc(DBPaperV2.created_at))
            .limit(limit)
            .offset(offset)
        )
        papers = result.scalars().all()
        return [self._to_dict(p) for p in papers], total

    async def get_stats(self) -> Dict[str, int]:
        total_result = await self.session.execute(select(func.count(DBPaperV2.id)))
        total_papers = total_result.scalar() or 0

        keyword_result = await self.session.execute(
            select(func.count(DBPaperKeywordV2.id))
        )
        total_keywords = keyword_result.scalar() or 0

        seven_days_ago = int(time.time()) - 7 * 24 * 60 * 60
        recent_result = await self.session.execute(
            select(func.count(DBPaperV2.id)).where(
                DBPaperV2.created_at >= seven_days_ago
            )
        )
        recent_papers = recent_result.scalar() or 0

        return {
            "total_papers": total_papers,
            "total_keywords": total_keywords,
            "recent_papers": recent_papers,
        }

    async def delete_paper(self, entry_id: str) -> bool:
        result = await self.session.execute(
            select(DBPaperV2).where(DBPaperV2.entry_id == entry_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return False
        await self.session.delete(paper)
        await self.session.commit()
        logger.info(f"删除论文: {paper.title}")
        return True

    @staticmethod
    def _to_dict(paper: DBPaperV2) -> Dict[str, Any]:
        arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
        return {
            "id": paper.id,
            "entry_id": paper.entry_id,
            "arxiv_id": arxiv_id,
            "title": paper.title,
            "authors": json.loads(paper.authors),
            "summary": paper.summary,
            "published": paper.published,
            "published_date": paper.published,
            "updated": paper.updated,
            "pdf_url": paper.pdf_url,
            "primary_category": paper.primary_category,
            "categories": json.loads(paper.categories),
            "links": json.loads(paper.links),
            "created_at": paper.created_at,
            "updated_at": paper.updated_at,
        }
