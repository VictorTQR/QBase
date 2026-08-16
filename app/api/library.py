"""知识库与资产相关 REST API。

同步 def 端点由 FastAPI 自动放入线程池执行，不阻塞事件循环。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_conn
from app.repositories.asset_repository import count_assets, list_assets
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
