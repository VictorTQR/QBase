import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from mineru.task_manager import task_manager
from mineru.client import mineru_client
from models.schemas import (
    TaskResponse,
    ErrorResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    TaskListResponse,
    StatsResponse,
    OperationResponse,
)
from utils.zip_handler import extract_markdown_from_zip
from database import get_db
from utils.file_hash import compute_bytes_hash

router = APIRouter(prefix="/api/mineru", tags=["MinerU"])


class LocalFileParseRequest(BaseModel):
    file_path: str


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(request: DuplicateCheckRequest):
    """检查文件是否已解析"""
    try:
        if request.file_hash:
            file_hash = request.file_hash
        elif request.file_path:
            from utils.file_hash import compute_file_hash

            file_hash = await compute_file_hash(request.file_path)
        else:
            raise HTTPException(
                status_code=400, detail="必须提供 file_hash 或 file_path"
            )

        existing_task = await task_manager.check_duplicate(file_hash)
        return DuplicateCheckResponse(
            is_duplicate=existing_task is not None,
            existing_task=TaskResponse(**existing_task) if existing_task else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"去重检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse", response_model=TaskResponse)
async def parse_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        file_content = await file.read()
        file_hash = compute_bytes_hash(file_content)

        # 检查是否已解析
        existing = await task_manager.check_duplicate(file_hash)
        if existing:
            return TaskResponse(**existing, is_duplicate=True)

        files = [{"name": file.filename}]
        apply_result = await mineru_client.batch_apply_upload_urls(files)
        batch_id = apply_result["batch_id"]
        upload_url = apply_result["file_urls"][0]

        await mineru_client.upload_file(upload_url, file_content)

        task = await task_manager.create_task(
            batch_id=batch_id,
            file_name=file.filename or "unknown",
            file_content=file_content,
            file_hash=file_hash,
        )

        background_tasks.add_task(task_manager.poll_task_status, task["id"])

        return TaskResponse(**task)

    except Exception as e:
        logger.error(f"解析文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-local", response_model=TaskResponse)
async def parse_local_document(
    background_tasks: BackgroundTasks,
    request: LocalFileParseRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 先检查去重
        from utils.file_hash import compute_file_hash

        file_hash = await compute_file_hash(file_path)
        existing = await task_manager.check_duplicate(file_hash)
        if existing:
            return TaskResponse(**existing, is_duplicate=True)

        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()

        files = [{"name": file_path.name}]
        apply_result = await mineru_client.batch_apply_upload_urls(files)
        batch_id = apply_result["batch_id"]
        upload_url = apply_result["file_urls"][0]

        await mineru_client.upload_file(upload_url, file_content)

        task = await task_manager.create_task(
            batch_id=batch_id,
            file_name=file_path.name or "unknown",
            file_path=str(file_path),
            file_content=file_content,
            file_hash=file_hash,
        )

        background_tasks.add_task(task_manager.poll_task_status, task["id"])

        return TaskResponse(**task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析本地文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse(**task)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(limit: int = 100, offset: int = 0):
    """分页获取任务列表"""
    tasks = await task_manager.list_tasks(limit, offset)
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_parse_stats():
    """获取解析统计"""
    stats = await task_manager.get_stats()
    return StatsResponse(**stats)


@router.get("/tasks/{task_id}/result")
async def get_parse_result(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["state"] != "done":
        raise HTTPException(status_code=400, detail="任务未完成")

    # 检查是否已有 markdown_content
    if task.get("markdown_content"):
        return {"markdown_content": task["markdown_content"]}

    try:
        # 重新从 MinerU 查询获取结果
        result = await mineru_client.batch_query_results(task["batch_id"])

        if "extract_result" not in result or len(result["extract_result"]) == 0:
            raise HTTPException(status_code=500, detail="无法从 MinerU 获取结果")

        file_result = result["extract_result"][0]

        if "full_zip_url" not in file_result:
            raise HTTPException(
                status_code=500, detail="MinerU 结果中缺少 full_zip_url"
            )

        zip_url = file_result["full_zip_url"]
        zip_content = await mineru_client.download_zip(zip_url)

        markdown_content = extract_markdown_from_zip(zip_content)

        storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(zip_content)

        # 更新数据库，保存 markdown_content 和 result_file_path
        await task_manager.update_task(
            task_id,
            markdown_content=markdown_content,
            result_file_path=storage_path,
            result_file_format="zip",
        )

        return {"markdown_content": markdown_content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取解析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/download")
async def download_zip(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["state"] != "done":
        raise HTTPException(status_code=400, detail="任务未完成")

    storage_path = task.get("result_file_path")
    if not storage_path or not os.path.exists(storage_path):
        storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")

    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    with open(storage_path, "rb") as f:
        file_content = f.read()

    file_format = task.get("result_file_format", "zip")
    media_type = (
        "application/zip" if file_format == "zip" else "application/octet-stream"
    )

    return Response(
        content=file_content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={task['file_name']}.{file_format}"
        },
    )


@router.delete("/tasks/clear-completed", response_model=OperationResponse)
async def clear_completed_tasks():
    """清除已完成的任务"""
    try:
        count = await task_manager.clear_completed()
        return OperationResponse(
            success=True, count=count, message=f"已清除 {count} 个已完成任务"
        )
    except Exception as e:
        logger.error(f"清除已完成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/clear-all", response_model=OperationResponse)
async def clear_all_tasks():
    """清空所有任务"""
    try:
        count = await task_manager.clear_all()
        return OperationResponse(
            success=True, count=count, message=f"已清空 {count} 个任务"
        )
    except Exception as e:
        logger.error(f"清空任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/batch-parse-pending", response_model=OperationResponse)
async def batch_parse_pending(background_tasks: BackgroundTasks):
    """批量解析待处理文件"""
    try:
        count = await task_manager.batch_parse_pending(background_tasks)
        return OperationResponse(
            success=True, count=count, message=f"已启动 {count} 个待解析任务"
        )
    except Exception as e:
        logger.error(f"批量解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/retry-failed", response_model=OperationResponse)
async def retry_failed_tasks(background_tasks: BackgroundTasks):
    """重试失败的任务"""
    try:
        count = await task_manager.retry_failed(background_tasks)
        return OperationResponse(
            success=True, count=count, message=f"已重试 {count} 个失败任务"
        )
    except Exception as e:
        logger.error(f"重试失败任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
