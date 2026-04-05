"""论文服务层"""
from typing import List, Dict, Any, Optional
from loguru import logger

from .scraper import ArxivScraper
from .database import paper_database


class PaperService:
    """论文服务类，整合抓取器和数据库"""

    def __init__(self):
        """初始化服务"""
        self.scraper = ArxivScraper()
        self.database = paper_database
        logger.info("PaperService 初始化完成")

    async def search_and_save(
        self,
        keyword: str,
        max_results: int = 100,
        sort_by: str = "relevance",
    ) -> Dict[str, Any]:
        """
        搜索论文并保存到数据库

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            sort_by: 排序方式 (relevance 或 submitted_date)

        Returns:
            搜索结果字典，包含论文列表、总数、关键词等信息
        """
        try:
            # 搜索论文
            papers = await self.scraper.search_papers(
                keyword=keyword,
                max_results=max_results,
                sort_by=sort_by,
            )

            # 保存到数据库
            saved_count = 0
            skipped_count = 0
            for paper_data in papers:
                paper_id = self.database.save_paper(
                    paper_data=paper_data,
                    keyword=keyword,
                    sort_type=sort_by,
                )
                if paper_id:
                    saved_count += 1
                else:
                    skipped_count += 1

            logger.info(
                f"搜索完成: 关键词='{keyword}', "
                f"找到={len(papers)}, 新增={saved_count}, 已存在={skipped_count}"
            )

            return {
                "papers": papers,
                "total": len(papers),
                "saved": saved_count,
                "skipped": skipped_count,
                "keyword": keyword,
                "sort_by": sort_by,
            }

        except Exception as e:
            logger.error(f"搜索和保存论文时出错: {e}")
            raise

    async def search_papers_only(
        self,
        keyword: str,
        max_results: int = 100,
        sort_by: str = "relevance",
    ) -> Dict[str, Any]:
        """
        仅搜索论文，不保存

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            sort_by: 排序方式

        Returns:
            搜索结果字典
        """
        try:
            papers = await self.scraper.search_papers(
                keyword=keyword,
                max_results=max_results,
                sort_by=sort_by,
            )

            logger.info(f"搜索完成: 关键词='{keyword}', 找到={len(papers)}")

            return {
                "papers": papers,
                "total": len(papers),
                "keyword": keyword,
                "sort_by": sort_by,
            }
        except Exception as e:
            logger.error(f"搜索论文时出错: {e}")
            raise

    async def import_paper(
        self,
        entry_id: str,
        keyword: str,
        sort_type: str = "relevance",
    ) -> Optional[Dict[str, Any]]:
        """
        通过论文 ID 导入单篇论文

        Args:
            entry_id: 论文 entry_id
            keyword: 搜索关键词（用于记录来源）
            sort_type: 排序类型（用于记录来源）

        Returns:
            导入的论文数据，如果已存在或失败则返回 None
        """
        try:
            # 从 arXiv 获取论文
            paper_data = await self.scraper.get_paper_by_id(entry_id)
            if not paper_data:
                logger.warning(f"未找到论文: {entry_id}")
                return None

            # 保存到数据库
            paper_id = self.database.save_paper(
                paper_data=paper_data,
                keyword=keyword,
                sort_type=sort_type,
            )

            if paper_id:
                logger.info(f"成功导入论文: {paper_data['title']}")
                return paper_data
            else:
                logger.info(f"论文已存在: {paper_data['title']}")
                return None

        except Exception as e:
            logger.error(f"导入论文时出错: {e}")
            raise

    def get_saved_papers(
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取已保存的论文列表

        Args:
            limit: 每页数量
            offset: 偏移量

        Returns:
            论文列表字典
        """
        try:
            papers = self.database.list_papers(limit=limit, offset=offset)
            return {
                "papers": papers,
                "total": len(papers),
                "offset": offset,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"获取已保存论文时出错: {e}")
            raise

    def get_paper_by_entry_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单篇已保存的论文

        Args:
            entry_id: 论文 entry_id

        Returns:
            论文字典，未找到则返回 None
        """
        try:
            return self.database.get_paper_by_entry_id(entry_id)
        except Exception as e:
            logger.error(f"获取论文时出错: {e}")
            raise

    def get_paper_stats(self) -> Dict[str, int]:
        """
        获取论文统计信息

        Returns:
            统计信息字典
        """
        try:
            return self.database.get_stats()
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            raise

    def delete_paper(self, entry_id: str) -> bool:
        """
        删除已保存的论文

        Args:
            entry_id: 论文 entry_id

        Returns:
            是否成功删除
        """
        try:
            return self.database.delete_paper(entry_id)
        except Exception as e:
            logger.error(f"删除论文时出错: {e}")
            raise


# 导出单例
paper_service = PaperService()
