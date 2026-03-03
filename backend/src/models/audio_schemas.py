from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class AudioTaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CHUNKING = "chunking"
    TRANSCRIBING = "transcribing"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioTranscriptionRequest(BaseModel):
    file_path: str = Field(..., description="音频文件路径")
    model: Optional[str] = Field(None, description="ASR 模型名称")
    api_key: Optional[str] = Field(None, description="硅基流动 API Key")
    base_url: Optional[str] = Field(None, description="硅基流动 API Base URL")


class AudioChunkInfo(BaseModel):
    chunk_id: str
    file_path: str
    start_time: float  # 秒
    end_time: float
    duration: float
    status: AudioTaskStatus = AudioTaskStatus.PENDING
    transcription: Optional[str] = None
    error: Optional[str] = None


class AudioTaskInfo(BaseModel):
    task_id: str
    file_path: str
    file_name: str
    total_duration: float  # 总时长（秒）
    total_size: int  # 总大小（字节）
    status: AudioTaskStatus
    chunks: List[AudioChunkInfo] = Field(default_factory=list)
    transcription: Optional[str] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float


class AudioTranscriptionResponse(BaseModel):
    task_id: str
    status: AudioTaskStatus
    message: str
