from fastapi import APIRouter, HTTPException
from loguru import logger

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.audio_schemas import (
    AudioTranscriptionRequest,
    AudioTranscriptionResponse,
    AudioTaskInfo,
)
from audio.task_manager import audio_task_manager
from processors import AudioProcessor
from audio.chunker import AudioChunker

router = APIRouter(prefix="/api/audio", tags=["audio"])

# 初始化处理器
audio_processor = AudioProcessor(
    task_manager=audio_task_manager, chunker=AudioChunker()
)


@router.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(request: AudioTranscriptionRequest):
    """创建音频转录任务"""
    try:
        logger.info(f"收到转录请求: {request.file_path}")

        result = await audio_processor.process(
            request.file_path,
            config={
                "api_key": request.api_key,
                "base_url": request.base_url,
                "model": request.model,
            },
        )

        return AudioTranscriptionResponse(**result)

    except Exception as e:
        logger.error(f"转录请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=AudioTaskInfo)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = audio_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    tasks = audio_task_manager.get_all_tasks()
    return {"total": len(tasks), "tasks": list(tasks.values())}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    task = audio_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    audio_task_manager.remove_task(task_id)
    return {"message": "任务已删除"}
