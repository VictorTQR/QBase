from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.workspace_service import QBaseWorkspaceService

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class InitializeWorkspaceRequest(BaseModel):
    workspace_path: str


@router.post("/initialize")
async def initialize_workspace(request: InitializeWorkspaceRequest):
    """初始化工作区 .qbase 目录"""
    try:
        service = QBaseWorkspaceService(request.workspace_path)
        success = service.initialize_workspace()
        if success:
            return {"success": True, "message": "工作区初始化成功"}
        else:
            raise HTTPException(status_code=500, detail="工作区初始化失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-initialized")
async def check_initialized(workspace_path: str):
    """检查工作区是否已初始化"""
    service = QBaseWorkspaceService(workspace_path)
    return {"initialized": service.is_initialized()}
