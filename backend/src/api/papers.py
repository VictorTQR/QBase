"""论文管理 API 路由"""

from fastapi import APIRouter
from loguru import logger

from models.paper_schemas import PaperSearchRequest, ImportPaperRequest
from papers.service import paper_service

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/search")
async def search_papers(request: PaperSearchRequest):
    try:
        result = await paper_service.search_papers_only(
            keyword=request.keyword,
            max_results=request.max_results,
            sort_by=request.sort_by,
        )
        return {"success": True, "data": result, "message": "搜索成功"}
    except Exception as e:
        logger.error(f"搜索论文失败: {e}")
        return {"success": False, "data": None, "message": f"搜索失败: {str(e)}"}


@router.post("/save")
async def save_papers(request: PaperSearchRequest):
    try:
        result = await paper_service.search_and_save(
            keyword=request.keyword,
            max_results=request.max_results,
            sort_by=request.sort_by,
        )
        return {
            "success": True,
            "data": result,
            "message": f"保存完成：新增{result.get('saved', 0)}篇，跳过{result.get('skipped', 0)}篇",
        }
    except Exception as e:
        logger.error(f"保存论文失败: {e}")
        return {"success": False, "data": None, "message": f"保存失败: {str(e)}"}


@router.get("/list")
async def list_saved_papers(limit: int = 100, offset: int = 0):
    try:
        result = paper_service.get_saved_papers(limit=limit, offset=offset)
        return {"success": True, "data": result, "message": "获取成功"}
    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        return {"success": False, "data": None, "message": f"获取失败: {str(e)}"}


@router.get("/stats")
async def get_paper_statistics():
    try:
        result = paper_service.get_paper_stats()
        return {"success": True, "data": result, "message": "获取成功"}
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {"success": False, "data": None, "message": f"获取失败: {str(e)}"}


@router.post("/import")
async def import_paper(request: ImportPaperRequest):
    try:
        result = await paper_service.import_paper(
            entry_id=request.entry_id,
            keyword="manual_import",
            sort_type="relevance",
        )
        if result:
            return {"success": True, "data": result, "message": "导入成功"}
        else:
            return {"success": False, "data": None, "message": "论文已存在或导入失败"}
    except Exception as e:
        logger.error(f"导入论文失败: {e}")
        return {"success": False, "data": None, "message": f"导入失败: {str(e)}"}


@router.get("/paper/{entry_id}")
async def get_paper(entry_id: str):
    try:
        result = paper_service.get_paper_by_entry_id(entry_id)
        if result:
            return {"success": True, "data": result, "message": "获取成功"}
        else:
            return {"success": False, "data": None, "message": "论文未找到"}
    except Exception as e:
        logger.error(f"获取论文详情失败: {e}")
        return {"success": False, "data": None, "message": f"获取失败: {str(e)}"}


@router.delete("/paper/{entry_id}")
async def delete_paper(entry_id: str):
    try:
        success = paper_service.delete_paper(entry_id)
        if success:
            return {"success": True, "data": None, "message": "删除成功"}
        else:
            return {"success": False, "data": None, "message": "论文未找到"}
    except Exception as e:
        logger.error(f"删除论文失败: {e}")
        return {"success": False, "data": None, "message": f"删除失败: {str(e)}"}
