from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from src.utils.file_hash import compute_file_hash

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

        hash_value = compute_file_hash(str(file_path))
        return {"success": True, "hash": hash_value, "file_path": request.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
