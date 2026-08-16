"""知识库与资产相关 REST API。

同步 def 端点由 FastAPI 自动放入线程池执行，不阻塞事件循环。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import count_assets, get_asset_by_id, list_assets
from app.services.library_service import (
    close_library,
    get_library_status,
    open_library,
)
from app.services.scanner_service import scan_current_library
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
