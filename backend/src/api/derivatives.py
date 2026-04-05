from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.services.workspace_service import QBaseWorkspaceService

router = APIRouter(prefix="/api/derivatives", tags=["derivatives"])


class SaveDerivativeRequest(BaseModel):
    workspace_path: str
    file_hash: str
    derivative_type: str
    content: Any
    model_used: Optional[str] = None
    version: int = 1


async def get_session():
    async with async_session() as session:
        yield session


@router.post("/save")
async def save_derivative(
    request: SaveDerivativeRequest, session: AsyncSession = Depends(get_session)
):
    """保存派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(request.workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)

        derivative = await derivative_service.save_derivative(
            file_hash=request.file_hash,
            derivative_type=request.derivative_type,
            content=request.content,
            model_used=request.model_used,
            version=request.version,
        )

        return {
            "success": True,
            "message": "派生数据保存成功",
            "derivative": {
                "id": derivative.id,
                "file_hash": derivative.file_hash,
                "type": derivative.type,
                "version": derivative.version,
                "model_used": derivative.model_used,
                "status": derivative.status,
                "created_at": derivative.created_at,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load")
async def load_derivative(
    workspace_path: str,
    file_hash: str,
    derivative_type: str,
    session: AsyncSession = Depends(get_session),
):
    """加载派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)

        content = await derivative_service.load_derivative(
            file_hash=file_hash,
            derivative_type=derivative_type,
        )

        if content is None:
            raise HTTPException(status_code=404, detail="派生数据不存在")

        return {
            "success": True,
            "file_hash": file_hash,
            "derivative_type": derivative_type,
            "content": content,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_derivatives(
    workspace_path: str, file_hash: str, session: AsyncSession = Depends(get_session)
):
    """列出文件的所有派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)

        derivatives = await derivative_service.list_derivatives(file_hash)

        return {
            "success": True,
            "file_hash": file_hash,
            "derivatives": derivatives,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_derivative(
    workspace_path: str,
    file_hash: str,
    derivative_type: str,
    session: AsyncSession = Depends(get_session),
):
    """删除派生数据"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)

        success = await derivative_service.delete_derivative(
            file_hash=file_hash,
            derivative_type=derivative_type,
        )

        if not success:
            raise HTTPException(status_code=404, detail="派生数据不存在")

        return {
            "success": True,
            "message": "派生数据删除成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-outdated")
async def mark_outdated(
    workspace_path: str, file_hash: str, session: AsyncSession = Depends(get_session)
):
    """标记文件的所有派生数据为过期"""
    try:
        workspace_service = QBaseWorkspaceService(workspace_path)
        derivative_service = workspace_service.get_derivative_service(session)

        count = await derivative_service.mark_outdated(file_hash)

        return {
            "success": True,
            "message": f"已标记 {count} 个派生数据为过期",
            "count": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
