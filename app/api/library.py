"""知识库与资产相关 REST API。

同步 def 端点由 FastAPI 自动放入线程池执行，不阻塞事件循环。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import count_assets, get_asset_by_id, list_assets
from app.repositories.task_repository import get_task, list_tasks
from app.services.library_service import (
    close_library,
    get_library_status,
    open_library,
)
from app.services.index_service import rebuild_fulltext_index
from app.services.scanner_service import scan_current_library
from app.services.search_service import search
from app.services.transcription_service import start_transcription
from app.services.vector_service import rebuild_vector_index
from app.state import get_db_path

router = APIRouter(prefix="/api")


class OpenLibraryRequest(BaseModel):
    path: str


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
    """获取单个资产详情及其派生文件。"""
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
        }
    finally:
        conn.close()


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
def api_search(q: str, mode: str = "fulltext", limit: int = 50) -> dict:
    """搜索：mode 为 filename / fulltext / vector。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    if mode not in ("filename", "fulltext", "vector"):
        raise HTTPException(
            status_code=400, detail="mode 仅支持 filename / fulltext / vector"
        )

    try:
        return {"query": q, "mode": mode, "items": search(q, mode, limit=limit)}
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
