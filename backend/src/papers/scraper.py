"""arXiv 论文抓取器"""

import asyncio
from typing import List, Optional
from loguru import logger
import arxiv


class ArxivScraper:
    """arXiv 论文抓取器"""

    def __init__(self):
        """初始化抓取器"""
        self.client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
        logger.info("ArxivScraper 初始化完成")

    def _convert_paper_to_dict(self, paper: arxiv.Result) -> dict:
        """将 arXiv 论文对象转换为字典"""
        arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
        return {
            "entry_id": paper.entry_id,
            "arxiv_id": arxiv_id,
            "title": paper.title,
            "authors": [a.name for a in paper.authors],
            "summary": paper.summary.replace("\n", " ").strip(),
            "published": paper.published.isoformat(),
            "published_date": paper.published.isoformat(),
            "updated": paper.updated.isoformat(),
            "pdf_url": paper.pdf_url,
            "primary_category": paper.primary_category,
            "categories": list(paper.categories),
            "links": [{"type": link.type, "href": link.href} for link in paper.links],
        }

    async def search_papers(
        self,
        keyword: str,
        max_results: int = 100,
        sort_by: str = "relevance",
    ) -> List[dict]:
        """
        搜索 arXiv 论文

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            sort_by: 排序方式 (relevance 或 submitted_date)

        Returns:
            论文列表
        """
        try:
            # 选择排序方式
            if sort_by == "submitted_date":
                sort_criterion = arxiv.SortCriterion.SubmittedDate
                order = arxiv.SortOrder.Descending
            else:  # relevance
                sort_criterion = arxiv.SortCriterion.Relevance
                order = arxiv.SortOrder.Descending

            # 构建搜索查询
            sort = arxiv.Sort(sort_criterion=sort_criterion, order=order)

            # 创建搜索
            search = arxiv.Search(
                query=keyword,
                max_results=max_results,
                sort=sort,
            )

            # 执行搜索（在线程池中运行以避免阻塞）
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, lambda: list(self.client.results(search))
            )

            # 转换结果
            papers = [self._convert_paper_to_dict(paper) for paper in results]

            logger.info(
                f"搜索关键词 '{keyword}' 完成，找到 {len(papers)} 篇论文 "
                f"(排序: {sort_by})"
            )
            return papers

        except Exception as e:
            logger.error(f"搜索 arXiv 论文时出错: {e}")
            raise

    async def get_paper_by_id(self, paper_id: str) -> Optional[dict]:
        """
        通过论文 ID 获取单篇论文

        Args:
            paper_id: 论文 ID (例如: "2301.07041")

        Returns:
            论文字典，如果未找到则返回 None
        """
        try:
            # 构建搜索查询（通过 ID 搜索）
            search = arxiv.Search(id_list=[paper_id])

            # 执行搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, lambda: list(self.client.results(search))
            )

            if not results:
                logger.warning(f"未找到论文 ID: {paper_id}")
                return None

            # 返回第一篇论文
            paper = self._convert_paper_to_dict(results[0])
            logger.info(f"成功获取论文: {paper['title']}")
            return paper

        except Exception as e:
            logger.error(f"获取论文 {paper_id} 时出错: {e}")
            raise
