import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger
import aiofiles

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from mineru.task_manager import task_manager
from mineru.client import mineru_client
from models.schemas import TaskResponse, ErrorResponse
from utils.zip_handler import extract_markdown_from_zip

router = APIRouter(prefix="/api/mineru", tags=["MinerU"])


class LocalFileParseRequest(BaseModel):
    file_path: str


@router.post("/parse", response_model=TaskResponse)
async def parse_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    try:
        file_content = await file.read()
        files = [{"name": file.filename}]

        apply_result = await mineru_client.batch_apply_upload_urls(files)
        batch_id = apply_result["batch_id"]
        upload_url = apply_result["file_urls"][0]

        await mineru_client.upload_file(upload_url, file_content)

        task = task_manager.create_task(batch_id, file.filename or "unknown")

        background_tasks.add_task(task_manager.poll_task_status, task["id"])

        return task

    except Exception as e:
        logger.error(f"解析文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-local", response_model=TaskResponse)
async def parse_local_document(
    background_tasks: BackgroundTasks,
    request: LocalFileParseRequest,
):
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()

        files = [{"name": file_path.name}]
        apply_result = await mineru_client.batch_apply_upload_urls(files)
        batch_id = apply_result["batch_id"]
        upload_url = apply_result["file_urls"][0]

        await mineru_client.upload_file(upload_url, file_content)
        task = task_manager.create_task(batch_id, file_path.name or "unknown")
        background_tasks.add_task(task_manager.poll_task_status, task["id"])

        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析本地文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/tasks/{task_id}/result")
async def get_parse_result(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["state"] != "done":
        raise HTTPException(status_code=400, detail="任务未完成")

    try:
        zip_url = task["result"]["full_zip_url"]
        zip_content = await mineru_client.download_zip(zip_url)

        markdown_content = extract_markdown_from_zip(zip_content)

        storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(zip_content)

        return {"markdown_content": markdown_content}
    except Exception as e:
        logger.error(f"获取解析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/download")
async def download_zip(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["state"] != "done":
        raise HTTPException(status_code=400, detail="任务未完成")

    storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")
    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="ZIP 文件不存在")

    with open(storage_path, "rb") as f:
        zip_content = f.read()

    return Response(
        content=zip_content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={task['file_name']}.zip"
        },
    )
