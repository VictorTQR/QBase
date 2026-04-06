from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.workspace_service import QBaseWorkspaceService
from src.services.file_scanner import FileScanner
from src.services.database_service import WorkspaceDatabaseService

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class InitializeWorkspaceRequest(BaseModel):
    workspace_path: str


class ScanWorkspaceRequest(BaseModel):
    workspace_path: str
    force_hash: bool = False


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


@router.post("/scan")
async def scan_workspace(request: ScanWorkspaceRequest):
    """扫描工作区文件"""
    try:
        workspace_service = QBaseWorkspaceService(request.workspace_path)
        if not workspace_service.is_initialized():
            workspace_service.initialize_workspace()

        await WorkspaceDatabaseService.init_workspace_db(request.workspace_path)

        session_factory = WorkspaceDatabaseService.get_session_factory(
            request.workspace_path
        )
        async with session_factory() as session:
            scanner = FileScanner(request.workspace_path, session)
            stats = await scanner.scan_full(force_hash=request.force_hash)

        return {"success": True, "message": "扫描完成", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
