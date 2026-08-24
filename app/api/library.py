"""知识库与资产相关 REST API。

同步 def 端点由 FastAPI 自动放入线程池执行，不阻塞事件循环。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import count_assets, get_asset_by_id, list_assets
from app.repositories.tag_repository import get_tags_for_asset
from app.repositories.task_repository import get_task, list_tasks
from app.services.library_service import (
    close_library,
    create_sidecar_dir,
    get_library_status,
    open_library,
)
from app.services.analysis_preset_service import list_analysis_presets
from app.services.analysis_service import (
    start_analysis,
    start_batch_analysis,
)
from app.services.index_service import rebuild_fulltext_index
from app.services.parse_service import start_parsing
from app.services.scanner_service import scan_current_library
from app.services.search_service import search, search_hybrid
from app.services.summarization_service import (
    start_batch_summarization,
    start_summarization,
)
from app.services.tag_service import (
    get_all_tags,
    set_asset_tags,
    start_batch_tagging,
    suggest_asset_tags,
)
from app.services.transcription_service import start_transcription
from app.services.vector_service import rebuild_vector_index
from app.state import get_db_path

router = APIRouter(prefix="/api")


class OpenLibraryRequest(BaseModel):
    path: str


class SetAssetTagsRequest(BaseModel):
    tags: list[str]


class BatchSummarizeRequest(BaseModel):
    asset_ids: list[str]
    overwrite: bool = False


class BatchTagRequest(BaseModel):
    asset_ids: list[str]


class AnalyzeRequest(BaseModel):
    preset_id: str


class BatchAnalyzeRequest(BaseModel):
    asset_ids: list[str]
    preset_id: str
    overwrite: bool = False


@router.post("/library/open")
def api_open_library(req: OpenLibraryRequest) -> dict:
    try:
        result = open_library(req.path)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/library/close")
def api_close_library() -> dict:
    close_library()
    return {"opened": False}


@router.get("/library/status")
def api_library_status() -> dict:
    return get_library_status()


@router.post("/library/scan")
def api_scan_library() -> dict:
    try:
        return scan_current_library()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/assets")
def api_list_assets(type: str | None = None, limit: int = 1000) -> dict:
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    conn = get_conn(get_db_path())
    try:
        return {
            "total": count_assets(conn, type),
            "items": list_assets(conn, limit=limit, asset_type=type),
        }
    finally:
        conn.close()


@router.get("/assets/{asset_id}")
def api_get_asset(asset_id: str) -> dict:
    """获取单个资产详情及其派生文件与标签。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    conn = get_conn(get_db_path())
    try:
        asset = get_asset_by_id(conn, asset_id)

        if asset is None:
            raise HTTPException(status_code=404, detail="资产不存在")

        return {
            "asset": asset,
            "artifacts": list_artifacts_by_asset(conn, asset_id),
            "tags": get_tags_for_asset(conn, asset_id),
        }
    finally:
        conn.close()


@router.get("/tags")
def api_list_tags() -> dict:
    """全部标签 + 使用数（m15）。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    return {"items": get_all_tags()}


@router.put("/assets/{asset_id}/tags")
def api_set_asset_tags(asset_id: str, req: SetAssetTagsRequest) -> dict:
    """整体替换资产标签（m15）：不存在的标签名自动创建，零引用标签自动清理。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    conn = get_conn(get_db_path())
    try:
        if get_asset_by_id(conn, asset_id) is None:
            raise HTTPException(status_code=404, detail="资产不存在")
    finally:
        conn.close()

    try:
        tags = set_asset_tags(asset_id, req.tags)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"tags": tags}


@router.post("/assets/{asset_id}/suggest-tags")
def api_suggest_asset_tags(asset_id: str) -> dict:
    """AI 建议标签（m16）：只返回建议，不写库；400 未启用/无输入文本。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    conn = get_conn(get_db_path())
    try:
        if get_asset_by_id(conn, asset_id) is None:
            raise HTTPException(status_code=404, detail="资产不存在")
    finally:
        conn.close()

    try:
        suggestions = suggest_asset_tags(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"suggestions": suggestions}


@router.post("/assets/batch-summarize")
def api_batch_summarize(req: BatchSummarizeRequest) -> dict:
    """批量总结（m17）：逐资产预检建任务，不合规项跳过；进度见任务中心。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    if not req.asset_ids:
        raise HTTPException(status_code=400, detail="未选择任何资产")

    try:
        return start_batch_summarization(req.asset_ids, overwrite=req.overwrite)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assets/batch-tag")
def api_batch_tag(req: BatchTagRequest) -> dict:
    """批量 AI 打标（m17）：建议清洗后自动追加写库，不删除已有标签。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    if not req.asset_ids:
        raise HTTPException(status_code=400, detail="未选择任何资产")

    try:
        return start_batch_tagging(req.asset_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analysis-presets")
def api_list_analysis_presets() -> dict:
    """分析模板列表（m18）：.knowledge/presets/ 下的全部可用模板。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    return {"items": list_analysis_presets()}


@router.post("/assets/{asset_id}/analyze")
def api_start_analysis(asset_id: str, req: AnalyzeRequest) -> dict:
    """触发生成深度分析任务（m18）：preset_id 指定分析模板。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        task_id = start_analysis(asset_id, req.preset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"task_id": task_id, "status": "pending"}


@router.post("/assets/batch-analyze")
def api_batch_analyze(req: BatchAnalyzeRequest) -> dict:
    """批量深度分析（m18）：同一模板逐资产预检建任务，不合规项跳过。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    if not req.asset_ids:
        raise HTTPException(status_code=400, detail="未选择任何资产")

    try:
        return start_batch_analysis(req.asset_ids, req.preset_id, overwrite=req.overwrite)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assets/{asset_id}/transcribe")
def api_start_transcription(asset_id: str) -> dict:
    """触发生成转录任务。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        task_id = start_transcription(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"task_id": task_id, "status": "pending"}


@router.post("/assets/{asset_id}/summarize")
def api_start_summarization(asset_id: str) -> dict:
    """触发生成总结任务。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        task_id = start_summarization(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"task_id": task_id, "status": "pending"}


@router.post("/assets/{asset_id}/parse")
def api_start_parsing(asset_id: str) -> dict:
    """触发生成文档解析任务。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        task_id = start_parsing(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"task_id": task_id, "status": "pending"}


@router.post("/assets/{asset_id}/sidecar-dir")
def api_create_sidecar_dir(asset_id: str) -> dict:
    """创建 <完整文件名>.kb 派生目录（m11 跟随现状 opt-in，只建目录不移动文件）。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        return create_sidecar_dir(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks")
def api_list_tasks(limit: int = 200) -> dict:
    """任务列表。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    conn = get_conn(get_db_path())
    try:
        return {"items": list_tasks(conn, limit=limit)}
    finally:
        conn.close()


@router.get("/tasks/{task_id}")
def api_get_task(task_id: str) -> dict:
    """单个任务详情。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    conn = get_conn(get_db_path())
    try:
        task = get_task(conn, task_id)

        if task is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        return task
    finally:
        conn.close()


@router.get("/search")
def api_search(
    q: str,
    mode: str = "hybrid",
    limit: int = 50,
    tag: list[str] = Query(default=[]),
) -> dict:
    """搜索：mode 为 filename / fulltext / vector / hybrid（全文+向量 RRF 融合）。

    tag 为可重复的标签过滤参数（m15，多选 OR）：&tag=AI&tag=播客。
    """
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    if mode not in ("filename", "fulltext", "vector", "hybrid"):
        raise HTTPException(
            status_code=400,
            detail="mode 仅支持 filename / fulltext / vector / hybrid",
        )

    tag_names = [t.strip() for t in tag if t.strip()] or None

    try:
        if mode == "hybrid":
            q = q.strip()

            if not q:
                return {"query": q, "mode": mode, "items": [], "degraded_reason": None}

            conn = get_conn(get_db_path())
            try:
                items, degraded_reason = search_hybrid(
                    conn, q, limit=limit, tag_names=tag_names
                )
            finally:
                conn.close()

            return {
                "query": q,
                "mode": mode,
                "items": items,
                "degraded_reason": degraded_reason,
            }

        return {
            "query": q,
            "mode": mode,
            "items": search(q, mode, limit=limit, tag_names=tag_names),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/search/rebuild")
def api_rebuild_index() -> dict:
    """手动重建全文索引。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        return rebuild_fulltext_index()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"索引重建失败：{exc}") from exc


@router.post("/search/vector/rebuild")
def api_rebuild_vector_index() -> dict:
    """手动重建向量索引（会调用 Embedding API，可能产生费用）。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        return rebuild_vector_index()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"向量索引重建失败：{exc}") from exc
