from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from sqlalchemy import select, desc

from src.models.db_models import DBFile
from src.repositories.file_repository import FileRepository
from src.services.database_service import WorkspaceDatabaseService
from src.utils.file_hash import compute_file_hash_sync

router = APIRouter(prefix="/api/files", tags=["files"])


class ComputeHashRequest(BaseModel):
    file_path: str


@router.post("/hash")
async def compute_hash(request: ComputeHashRequest):
    """计算文件哈希"""
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        hash_value = compute_file_hash_sync(str(file_path))
        return {"success": True, "hash": hash_value, "file_path": request.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_files(
    workspace_path: str,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
):
    """列出工作区文件"""
    try:
        session_factory = WorkspaceDatabaseService.get_session_factory(workspace_path)
        async with session_factory() as session:
            query = select(DBFile)
            if status:
                query = query.where(DBFile.status == status)
            query = query.order_by(desc(DBFile.updated_at)).offset(offset).limit(limit)

            result = await session.execute(query)
            files = result.scalars().all()

            file_list = []
            for f in files:
                file_list.append(
                    {
                        "hash": f.hash,
                        "rel_path": f.rel_path,
                        "file_type": f.file_type,
                        "size": f.size,
                        "mtime": f.mtime,
                        "status": f.status,
                        "created_at": f.created_at,
                        "updated_at": f.updated_at,
                        "absolute_path": str(Path(workspace_path) / f.rel_path)
                        if workspace_path
                        else None,
                    }
                )

            count_query = select(DBFile)
            if status:
                count_query = count_query.where(DBFile.status == status)
            count_result = await session.execute(count_query)
            total = len(count_result.scalars().all())

        return {
            "success": True,
            "files": file_list,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_hash}")
async def get_file(
    file_hash: str,
    workspace_path: Optional[str] = None,
):
    """获取单个文件信息"""
    try:
        session_factory = WorkspaceDatabaseService.get_session_factory(workspace_path)
        async with session_factory() as session:
            repo = FileRepository(session)
            db_file = await repo.get_by_hash(file_hash)

            if not db_file:
                raise HTTPException(status_code=404, detail="文件不存在")

        return {
            "success": True,
            "file": {
                "hash": db_file.hash,
                "rel_path": db_file.rel_path,
                "file_type": db_file.file_type,
                "size": db_file.size,
                "mtime": db_file.mtime,
                "status": db_file.status,
                "created_at": db_file.created_at,
                "updated_at": db_file.updated_at,
                "absolute_path": str(Path(workspace_path) / db_file.rel_path)
                if workspace_path
                else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_hash}")
async def delete_file(file_hash: str, workspace_path: Optional[str] = None):
    """删除文件记录（不删除物理文件）"""
    try:
        session_factory = WorkspaceDatabaseService.get_session_factory(workspace_path)
        async with session_factory() as session:
            repo = FileRepository(session)
            success = await repo.delete(file_hash)

            if not success:
                raise HTTPException(status_code=404, detail="文件不存在")

        return {"success": True, "message": "文件记录已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
