"""论文管理 API 路由"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Optional

from models.paper_schemas import (
    ArxivPaper,
    PaperSearchRequest,
    PaperSearchResponse,
    ImportPaperRequest,
    PaperListResponse,
    PaperStatsResponse,
    PaperSaveResponse,
)
from papers.service import paper_service

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/search", response_model=PaperSearchResponse)
async def search_papers(request: PaperSearchRequest):
    """
    搜索 arXiv 论文

    Args:
        request: 搜索请求参数

    Returns:
        搜索结果列表
    """
    try:
        logger.info(
            f"收到论文搜索请求: keyword='{request.keyword}', "
            f"max_results={request.max_results}, sort_by={request.sort_by}"
        )

        result = await paper_service.search_papers_only(
            keyword=request.keyword,
            max_results=request.max_results,
            sort_by=request.sort_by,
        )

        return PaperSearchResponse(**result)

    except Exception as e:
        logger.error(f"搜索论文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", response_model=PaperSaveResponse)
async def save_papers(request: PaperSearchRequest):
    """
    搜索并保存论文到数据库

    Args:
        request: 搜索请求参数

    Returns:
        保存结果统计
    """
    try:
        logger.info(
            f"收到论文搜索并保存请求: keyword='{request.keyword}', "
            f"max_results={request.max_results}, sort_by={request.sort_by}"
        )

        result = await paper_service.search_and_save(
            keyword=request.keyword,
            max_results=request.max_results,
            sort_by=request.sort_by,
        )

        return PaperSaveResponse(
            message="搜索并保存完成",
            total=result["total"],
            saved=result["saved"],
            skipped=result["skipped"],
            keyword=result["keyword"],
            sort_by=result["sort_by"],
        )

    except Exception as e:
        logger.error(f"保存论文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=PaperListResponse)
async def list_saved_papers(limit: int = 100, offset: int = 0):
    """
    获取已保存的论文列表

    Args:
        limit: 每页数量
        offset: 偏移量

    Returns:
        论文列表
    """
    try:
        logger.info(f"获取已保存论文列表: limit={limit}, offset={offset}")

        result = paper_service.get_saved_papers(limit=limit, offset=offset)

        return PaperListResponse(**result)

    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=PaperStatsResponse)
async def get_paper_statistics():
    """
    获取论文统计信息

    Returns:
        统计信息
    """
    try:
        logger.info("获取论文统计信息")

        stats = paper_service.get_paper_stats()

        return PaperStatsResponse(
            total_papers=stats["total_papers"],
            total_keywords=stats["total_keywords"],
            recent_papers=stats["recent_papers"],
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_paper(request: ImportPaperRequest):
    """
    通过论文 ID 导入单篇论文

    Args:
        request: 导入请求参数

    Returns:
        导入结果
    """
    try:
        logger.info(f"收到论文导入请求: entry_id='{request.entry_id}'")

        # 导入时使用默认的关键词和排序方式
        paper_data = await paper_service.import_paper(
            entry_id=request.entry_id,
            keyword="manual_import",  # 手动导入标记
            sort_type="relevance",
        )

        if paper_data:
            return {
                "message": "论文导入成功",
                "paper": ArxivPaper(**paper_data),
            }
        else:
            raise HTTPException(status_code=400, detail="论文已存在或导入失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入论文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paper/{entry_id}")
async def get_paper(entry_id: str):
    """
    获取单篇已保存的论文

    Args:
        entry_id: 论文 ID

    Returns:
        论文详情
    """
    try:
        logger.info(f"获取论文详情: entry_id='{entry_id}'")

        paper_data = paper_service.get_paper_by_entry_id(entry_id)

        if not paper_data:
            raise HTTPException(status_code=404, detail="论文不存在")

        return ArxivPaper(**paper_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取论文详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/paper/{entry_id}")
async def delete_paper(entry_id: str):
    """
    删除已保存的论文

    Args:
        entry_id: 论文 ID

    Returns:
        删除结果
    """
    try:
        logger.info(f"删除论文: entry_id='{entry_id}'")

        success = paper_service.delete_paper(entry_id)

        if not success:
            raise HTTPException(status_code=404, detail="论文不存在或删除失败")

        return {"message": "论文已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除论文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
