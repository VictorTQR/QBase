from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from loguru import logger

from models.audio_schemas import (
    AudioTranscriptionRequest,
    LocalAudioTranscriptionRequest,
    AudioTranscriptionResponse,
    AudioTaskInfo,
    AudioTaskStatus,
)
from audio.task_manager import audio_task_manager
from processors import AudioProcessor
from audio.chunker import AudioChunker

router = APIRouter(prefix="/api/audio", tags=["audio"])

# 初始化处理器
audio_processor = AudioProcessor(
    task_manager=audio_task_manager, chunker=AudioChunker()
)


@router.post("/transcribe-upload", response_model=AudioTranscriptionResponse)
async def transcribe_audio_upload(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
):
    """上传音频文件并创建转录任务"""
    try:
        import tempfile
        import os

        logger.debug(
            f"开始处理音频上传: {file.filename}, 内容类型: {file.content_type}"
        )

        suffix = Path(file.filename).suffix if file.filename else ".wav"
        logger.debug(f"使用文件后缀: {suffix}")

        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_file_path = tmp.name
                logger.debug(
                    f"临时文件已创建: {temp_file_path}, 大小: {len(content)} 字节"
                )
        except Exception as e:
            logger.error(f"创建临时文件失败: {e}")
            raise

        logger.info(f"收到音频上传: {file.filename}, 临时路径: {temp_file_path}")

        logger.debug("调用 audio_processor.process...")
        result = await audio_processor.process(
            temp_file_path,
            config={"model": model} if model else None,
            file_content=content,
        )
        logger.debug(f"audio_processor.process 返回结果: {result}")

        return AudioTranscriptionResponse(**result)

    except Exception as e:
        logger.exception(f"音频上传转录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-local", response_model=AudioTranscriptionResponse)
async def transcribe_audio_local(request: LocalAudioTranscriptionRequest):
    """通过本地文件路径创建音频转录任务"""
    try:
        logger.info(f"收到转录请求: {request.file_path}")

        result = await audio_processor.process(
            request.file_path,
            config={"model": request.model} if request.model else None,
        )

        return AudioTranscriptionResponse(**result)

    except Exception as e:
        logger.error(f"转录请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio_legacy(request: AudioTranscriptionRequest):
    """创建音频转录任务（向后兼容别名）"""
    try:
        logger.info(f"收到转录请求（兼容）: {request.file_path}")

        result = await audio_processor.process(
            request.file_path,
            config={"model": request.model} if request.model else None,
        )

        return AudioTranscriptionResponse(**result)

    except Exception as e:
        logger.error(f"转录请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=AudioTaskInfo)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = await audio_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/tasks/{task_id}/result")
async def get_transcription_result(task_id: str):
    """获取转录结果"""
    task = await audio_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != AudioTaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务未完成")

    return {
        "task_id": task_id,
        "transcription": task.transcription,
        "file_name": task.file_name,
        "total_duration": task.total_duration,
        "total_size": task.total_size,
        "created_at": task.created_at,
        "completed_at": task.updated_at,
    }


@router.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    tasks = await audio_task_manager.get_all_tasks()
    return {"total": len(tasks), "tasks": list(tasks.values())}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    task = await audio_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await audio_task_manager.remove_task(task_id)
    return {"message": "任务已删除"}
