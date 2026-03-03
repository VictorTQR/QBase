# 音频转录功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 实现基于硅基流动 API 的音频文件转录功能，支持大文件分块处理，采用插件化架构设计。

**架构：** 
- 后端 FastAPI 新增 `/api/audio/*` 路由
- 创建 `FileProcessor` 抽象层和 `AudioProcessor` 实现
- 插件化 ASR 提供商设计（硅基流动为第一个实现）
- 前端使用 `hook-fetch` 直接 HTTP 调用（与 PDF 解析一致，不经过 IPC）
- 复用现有存储方案（LocalStorage + IndexedDB）

**技术栈：** FastAPI, ffmpeg, httpx, Vue 3, Pinia, hook-fetch

---

## 任务清单

### 任务 1：后端配置和数据模型
**文件：**
- 修改: `backend/src/config.py`
- 创建: `backend/src/models/audio_schemas.py`
- 修改: `backend/src/models/__init__.py`

### 任务 2：ASR 提供商抽象和硅基流动实现
**文件：**
- 创建: `backend/src/audio/providers/base.py` (ASRProvider 抽象基类)
- 创建: `backend/src/audio/providers/siliconflow.py` (硅基流动实现)
- 创建: `backend/src/audio/providers/__init__.py`

### 任务 3：音频分块处理器
**文件：**
- 创建: `backend/src/audio/chunker.py` (ffmpeg 分块处理)
- 创建: `backend/src/audio/utils.py` (音频工具函数)

### 任务 4：FileProcessor 抽象层和 AudioProcessor
**文件：**
- 创建: `backend/src/processors/base.py` (FileProcessor 基类)
- 创建: `backend/src/processors/audio_processor.py` (AudioProcessor 实现)
- 创建: `backend/src/processors/__init__.py`

### 任务 5：音频任务管理器
**文件：**
- 创建: `backend/src/audio/task_manager.py` (任务状态管理)

### 任务 6：FastAPI 音频路由
**文件：**
- 创建: `backend/src/api/audio.py` (音频 API 路由)
- 修改: `backend/main.py` (注册路由)

### 任务 7：前端 audioApi 封装
**文件：**
- 修改: `app/src/utils/backend.js` (添加 AudioApi 类)

### 任务 8：前端 AudioTranscriber 实现
**文件：**
- 修改: `app/src/processors/parse/AudioTranscriber.js` (实现真正的转录逻辑)

### 任务 9：前端集成到解析流程
**文件：**
- 修改: `app/src/processors/parse/TextExtractor.js` (添加音频类型支持)

### 任务 10：UI 集成（解析管理页面）
**文件：**
- 修改: `app/src/views/ParseManagement.vue` (集成音频转录 UI)

---

## 详细任务步骤

### 任务 1：后端配置和数据模型

**Step 1: 修改 config.py 添加硅基流动配置**

```python
# backend/src/config.py
class Settings(BaseSettings):
    MINERU_API_KEY: str = ""
    MINERU_API_BASE_URL: str = "https://mineru.net"
    STORAGE_DIR: str = "./storage"
    TASK_POLL_INTERVAL: int = 3
    MAX_POLL_ATTEMPTS: int = 60
    
    # 硅基流动配置
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_API_BASE_URL: str = "https://api.siliconflow.cn"
    SILICONFLOW_ASR_MODEL: str = "FunAudioLLM/SenseVoiceSmall"
    
    # 音频分块配置
    AUDIO_CHUNK_DURATION_MINUTES: int = 50
    AUDIO_MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"
```

**Step 2: 创建 audio_schemas.py**

```python
# backend/src/models/audio_schemas.py
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
```

**Step 3: 更新 models/__init__.py**

```python
# backend/src/models/__init__.py
from .schemas import *
from .audio_schemas import *
```

---

### 任务 2：ASR 提供商抽象和硅基流动实现

**Step 1: 创建 base.py 抽象基类**

```python
# backend/src/audio/providers/base.py
from abc import ABC, abstractmethod
from typing import Optional


class ASRProvider(ABC):
    """ASR 提供商抽象基类"""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_file_path: str,
        model: Optional[str] = None
    ) -> str:
        """
        转录音频文件为文本
        
        Args:
            audio_file_path: 音频文件路径
            model: 模型名称（可选，覆盖默认配置）
            
        Returns:
            转录的文本内容
            
        Raises:
            Exception: 转录失败时抛出异常
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass
```

**Step 2: 创建 siliconflow.py 实现**

```python
# backend/src/audio/providers/siliconflow.py
import httpx
from pathlib import Path
from typing import Optional
from loguru import logger

from .base import ASRProvider
from config import settings


class SiliconFlowASRProvider(ASRProvider):
    """硅基流动 ASR 提供商实现"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.SILICONFLOW_API_KEY
        self.base_url = base_url or settings.SILICONFLOW_API_BASE_URL
        self.model = model or settings.SILICONFLOW_ASR_MODEL
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=300.0,  # 5 分钟超时
                follow_redirects=True
            )
        return self._client
    
    async def transcribe(
        self,
        audio_file_path: str,
        model: Optional[str] = None
    ) -> str:
        use_model = model or self.model
        client = await self._get_client()
        
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
        
        logger.info(f"开始转录音频: {audio_file_path}, 模型: {use_model}")
        
        with open(audio_file_path, 'rb') as f:
            files = {'file': (audio_path.name, f, 'audio/mpeg')}
            data = {'model': use_model}
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = await client.post(
                '/v1/audio/transcriptions',
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"硅基流动 API 错误: {response.status_code} - {response.text}")
                raise Exception(f"转录失败: {response.status_code} - {response.text}")
            
            result = response.json()
            transcription = result.get('text', '')
            logger.info(f"转录完成，文本长度: {len(transcription)}")
            return transcription
    
    def validate_config(self) -> bool:
        if not self.api_key:
            logger.error("硅基流动 API Key 未配置")
            return False
        if not self.base_url:
            logger.error("硅基流动 API Base URL 未配置")
            return False
        return True
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
```

**Step 3: 创建 providers/__init__.py**

```python
# backend/src/audio/providers/__init__.py
from .base import ASRProvider
from .siliconflow import SiliconFlowASRProvider

__all__ = ['ASRProvider', 'SiliconFlowASRProvider']
```

---

### 任务 3：音频分块处理器

**Step 1: 创建 chunker.py**

```python
# backend/src/audio/chunker.py
import asyncio
import subprocess
import uuid
from pathlib import Path
from typing import List, Tuple
from loguru import logger

from config import settings


class AudioChunker:
    """音频分块处理器，使用 ffmpeg"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.STORAGE_DIR) / "audio_chunks"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_duration = settings.AUDIO_CHUNK_DURATION_MINUTES * 60  # 转换为秒
    
    async def get_audio_duration(self, file_path: str) -> float:
        """获取音频文件时长（秒）"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"ffprobe 错误: {stderr.decode()}")
                raise Exception(f"无法获取音频时长: {stderr.decode()}")
            
            duration = float(stdout.decode().strip())
            return duration
        except FileNotFoundError:
            raise Exception("未找到 ffprobe，请安装 ffmpeg")
    
    async def get_audio_size(self, file_path: str) -> int:
        """获取音频文件大小（字节）"""
        return Path(file_path).stat().st_size
    
    async def chunk_audio(
        self,
        file_path: str,
        task_id: Optional[str] = None
    ) -> List[Tuple[str, float, float]]:
        """
        将音频文件分块
        
        Args:
            file_path: 原音频文件路径
            task_id: 任务 ID（用于生成 chunk 文件名）
            
        Returns:
            列表: [(chunk_file_path, start_time, end_time), ...]
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        duration = await self.get_audio_duration(file_path)
        logger.info(f"音频总时长: {duration:.2f} 秒, 分块时长: {self.chunk_duration} 秒")
        
        chunks = []
        num_chunks = int(duration / self.chunk_duration) + 1
        
        for i in range(num_chunks):
            start_time = i * self.chunk_duration
            end_time = min((i + 1) * self.chunk_duration, duration)
            
            chunk_file = self.storage_dir / f"{task_id}_chunk_{i:04d}.mp3"
            
            await self._split_audio(
                file_path,
                str(chunk_file),
                start_time,
                end_time - start_time
            )
            
            chunks.append((str(chunk_file), start_time, end_time))
            logger.info(f"创建分块 {i+1}/{num_chunks}: {chunk_file}")
        
        return chunks
    
    async def _split_audio(
        self,
        input_file: str,
        output_file: str,
        start_time: float,
        duration: float
    ):
        """使用 ffmpeg 分割音频"""
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',
            '-y',
            output_file
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"ffmpeg 错误: {stderr.decode()}")
            raise Exception(f"音频分块失败: {stderr.decode()}")
    
    def cleanup_chunks(self, task_id: str):
        """清理任务的分块文件"""
        pattern = f"{task_id}_chunk_*.mp3"
        for chunk_file in self.storage_dir.glob(pattern):
            try:
                chunk_file.unlink()
                logger.info(f"删除分块文件: {chunk_file}")
            except Exception as e:
                logger.error(f"删除分块文件失败 {chunk_file}: {e}")
```

**Step 2: 创建 utils.py**

```python
# backend/src/audio/utils.py
from pathlib import Path
from typing import Set

# 支持的音频扩展名
SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {
    '.mp3', '.wav', '.ogg', '.m4a', '.flac',
    '.aac', '.wma', '.opus', '.webm'
}


def is_audio_file(file_path: str) -> bool:
    """判断是否为音频文件"""
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_AUDIO_EXTENSIONS


def merge_transcriptions(chunk_transcriptions: list) -> str:
    """
    合并多个分块的转录文本
    
    Args:
        chunk_transcriptions: [(start_time, end_time, text), ...]
        
    Returns:
        合并后的文本
    """
    # 按开始时间排序
    sorted_chunks = sorted(chunk_transcriptions, key=lambda x: x[0])
    
    # 简单拼接
    merged = []
    for _, _, text in sorted_chunks:
        if text and text.strip():
            merged.append(text.strip())
    
    return '\n\n'.join(merged)
```

---

### 任务 4：FileProcessor 抽象层和 AudioProcessor

**Step 1: 创建 processors/base.py**

```python
# backend/src/processors/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional


class FileProcessor(ABC):
    """文件处理器抽象基类"""
    
    @abstractmethod
    async def process(
        self,
        file_path: str,
        config: Optional[dict] = None
    ) -> Any:
        """
        处理文件
        
        Args:
            file_path: 文件路径
            config: 配置参数
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """判断是否支持该文件类型"""
        pass
```

**Step 2: 创建 processors/audio_processor.py**

```python
# backend/src/processors/audio_processor.py
import time
import uuid
from pathlib import Path
from typing import Any, Optional
from loguru import logger

from .base import FileProcessor
from ..audio.providers import ASRProvider, SiliconFlowASRProvider
from ..audio.chunker import AudioChunker
from ..audio.task_manager import AudioTaskManager
from ..audio.utils import is_audio_file
from ..models.audio_schemas import (
    AudioTaskStatus,
    AudioChunkInfo,
    AudioTaskInfo
)


class AudioProcessor(FileProcessor):
    """音频文件处理器"""
    
    def __init__(
        self,
        task_manager: AudioTaskManager,
        chunker: Optional[AudioChunker] = None
    ):
        self.task_manager = task_manager
        self.chunker = chunker or AudioChunker()
    
    async def process(
        self,
        file_path: str,
        config: Optional[dict] = None
    ) -> dict:
        config = config or {}
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task = await self._create_task(task_id, file_path)
        
        # 启动后台处理（不阻塞请求）
        import asyncio
        asyncio.create_task(
            self._process_task(task_id, file_path, config)
        )
        
        return {
            'task_id': task_id,
            'status': AudioTaskStatus.PENDING,
            'message': '音频转录任务已创建'
        }
    
    async def _create_task(self, task_id: str, file_path: str) -> AudioTaskInfo:
        file_path_obj = Path(file_path)
        total_size = file_path_obj.stat().st_size
        total_duration = await self.chunker.get_audio_duration(file_path)
        
        task = AudioTaskInfo(
            task_id=task_id,
            file_path=file_path,
            file_name=file_path_obj.name,
            total_duration=total_duration,
            total_size=total_size,
            status=AudioTaskStatus.PENDING,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.task_manager.add_task(task)
        return task
    
    async def _process_task(
        self,
        task_id: str,
        file_path: str,
        config: dict
    ):
        try:
            task = self.task_manager.get_task(task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return
            
            # 更新状态为分块中
            task.status = AudioTaskStatus.CHUNKING
            task.updated_at = time.time()
            self.task_manager.update_task(task)
            
            # 1. 音频分块
            chunks = await self.chunker.chunk_audio(file_path, task_id)
            
            chunk_infos = []
            for i, (chunk_file, start, end) in enumerate(chunks):
                chunk_info = AudioChunkInfo(
                    chunk_id=f"{task_id}_chunk_{i}",
                    file_path=chunk_file,
                    start_time=start,
                    end_time=end,
                    duration=end - start,
                    status=AudioTaskStatus.PENDING
                )
                chunk_infos.append(chunk_info)
            
            task.chunks = chunk_infos
            task.status = AudioTaskStatus.TRANSCRIBING
            task.updated_at = time.time()
            self.task_manager.update_task(task)
            
            # 2. 创建 ASR 提供商
            provider = SiliconFlowASRProvider(
                api_key=config.get('api_key'),
                base_url=config.get('base_url'),
                model=config.get('model')
            )
            
            # 3. 逐块转录
            all_transcriptions = []
            for i, chunk_info in enumerate(chunk_infos):
                try:
                    chunk_info.status = AudioTaskStatus.TRANSCRIBING
                    task.updated_at = time.time()
                    self.task_manager.update_task(task)
                    
                    transcription = await provider.transcribe(
                        chunk_info.file_path,
                        model=config.get('model')
                    )
                    
                    chunk_info.transcription = transcription
                    chunk_info.status = AudioTaskStatus.COMPLETED
                    all_transcriptions.append((
                        chunk_info.start_time,
                        chunk_info.end_time,
                        transcription
                    ))
                    
                    logger.info(f"分块 {i+1}/{len(chunk_infos)} 转录完成")
                    
                except Exception as e:
                    chunk_info.status = AudioTaskStatus.FAILED
                    chunk_info.error = str(e)
                    logger.error(f"分块 {i+1} 转录失败: {e}")
                
                task.updated_at = time.time()
                self.task_manager.update_task(task)
            
            await provider.close()
            
            # 4. 合并转录结果
            task.status = AudioTaskStatus.MERGING
            task.updated_at = time.time()
            self.task_manager.update_task(task)
            
            from ..audio.utils import merge_transcriptions
            final_transcription = merge_transcriptions(all_transcriptions)
            task.transcription = final_transcription
            task.status = AudioTaskStatus.COMPLETED
            task.updated_at = time.time()
            self.task_manager.update_task(task)
            
            # 5. 清理分块文件
            self.chunker.cleanup_chunks(task_id)
            
            logger.info(f"任务 {task_id} 完成，转录文本长度: {len(final_transcription)}")
            
        except Exception as e:
            logger.error(f"任务 {task_id} 处理失败: {e}")
            task = self.task_manager.get_task(task_id)
            if task:
                task.status = AudioTaskStatus.FAILED
                task.error = str(e)
                task.updated_at = time.time()
                self.task_manager.update_task(task)
    
    def supports(self, file_path: str) -> bool:
        return is_audio_file(file_path)
```

**Step 3: 创建 processors/__init__.py**

```python
# backend/src/processors/__init__.py
from .base import FileProcessor
from .audio_processor import AudioProcessor

__all__ = ['FileProcessor', 'AudioProcessor']
```

---

### 任务 5：音频任务管理器

**Step 1: 创建 audio/task_manager.py**

```python
# backend/src/audio/task_manager.py
import threading
from typing import Dict, Optional
from loguru import logger

from ..models.audio_schemas import AudioTaskInfo


class AudioTaskManager:
    """音频任务管理器（内存存储，简单实现）"""
    
    _instance: Optional['AudioTaskManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, AudioTaskInfo] = {}
        return cls._instance
    
    def __init__(self):
        pass  # 单例，只在 __new__ 中初始化
    
    def add_task(self, task: AudioTaskInfo):
        """添加任务"""
        with self._lock:
            self._tasks[task.task_id] = task
            logger.info(f"添加音频任务: {task.task_id}")
    
    def get_task(self, task_id: str) -> Optional[AudioTaskInfo]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def update_task(self, task: AudioTaskInfo):
        """更新任务"""
        with self._lock:
            self._tasks[task.task_id] = task
    
    def remove_task(self, task_id: str):
        """移除任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"移除音频任务: {task_id}")
    
    def get_all_tasks(self) -> Dict[str, AudioTaskInfo]:
        """获取所有任务"""
        with self._lock:
            return dict(self._tasks)


# 全局单例实例
audio_task_manager = AudioTaskManager()
```

---

### 任务 6：FastAPI 音频路由

**Step 1: 创建 api/audio.py**

```python
# backend/src/api/audio.py
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models.audio_schemas import (
    AudioTranscriptionRequest,
    AudioTranscriptionResponse,
    AudioTaskInfo
)
from ..audio.task_manager import audio_task_manager
from ..processors import AudioProcessor
from ..audio.chunker import AudioChunker

router = APIRouter(prefix="/api/audio", tags=["audio"])

# 初始化处理器
audio_processor = AudioProcessor(
    task_manager=audio_task_manager,
    chunker=AudioChunker()
)


@router.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(request: AudioTranscriptionRequest):
    """创建音频转录任务"""
    try:
        logger.info(f"收到转录请求: {request.file_path}")
        
        result = await audio_processor.process(
            request.file_path,
            config={
                'api_key': request.api_key,
                'base_url': request.base_url,
                'model': request.model
            }
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
    return {
        "total": len(tasks),
        "tasks": list(tasks.values())
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    task = audio_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    audio_task_manager.remove_task(task_id)
    return {"message": "任务已删除"}
```

**Step 2: 修改 backend/main.py**

```python
# backend/main.py
from api.mineru import router as mineru_router
from api.audio import router as audio_router  # 新增

app = FastAPI(title="QBase Backend", version="0.1.0")

# ... CORS 配置 ...

app.include_router(mineru_router)
app.include_router(audio_router)  # 新增
```

---

### 任务 7：前端 audioApi 封装

**Step 1: 修改 app/src/utils/backend.js**

在 `MinerUApi` 类之后添加 `AudioApi` 类，并更新导出：

```javascript
// app/src/utils/backend.js
class AudioApi {
  constructor(backendService) {
    this.backend = backendService
  }

  async transcribeAudio(filePath, config = {}) {
    const request = this.backend.client.post('/api/audio/transcribe', {
      file_path: filePath,
      model: config.model,
      api_key: config.apiKey,
      base_url: config.baseUrl
    })
    return await request.json()
  }

  async getTaskStatus(taskId) {
    const request = this.backend.client.get(`/api/audio/tasks/${taskId}`)
    return await request.json()
  }

  async listTasks() {
    const request = this.backend.client.get('/api/audio/tasks')
    return await request.json()
  }

  async deleteTask(taskId) {
    const request = this.backend.client.delete(`/api/audio/tasks/${taskId}`)
    return await request.json()
  }
}

const backendService = new BackendService()
const mineruApi = new MinerUApi(backendService)
const audioApi = new AudioApi(backendService)  // 新增

export { backendService, mineruApi, audioApi, BackendService, MinerUApi, AudioApi }
export default backendService
```

---

### 任务 8：前端 AudioTranscriber 实现

**Step 1: 修改 app/src/processors/parse/AudioTranscriber.js**

```javascript
// app/src/processors/parse/AudioTranscriber.js
import { useAgentStore } from '@/stores/agent'
import { audioApi } from '@/utils/backend'

const POLL_INTERVAL = 3000
const MAX_POLL_ATTEMPTS = 600

export class AudioTranscriber {
  static async transcribe(filePath) {
    const agentStore = useAgentStore()
    const siliconflowConfig = agentStore.llmConfig.siliconflow || {}
    
    try {
      const result = await audioApi.transcribeAudio(filePath, {
        apiKey: siliconflowConfig.apiKey,
        baseUrl: siliconflowConfig.baseUrl,
        model: siliconflowConfig.asrModel
      })
      
      return await this._pollTask(result.task_id)
      
    } catch (error) {
      console.error('音频转录失败:', error)
      throw error
    }
  }
  
  static async _pollTask(taskId) {
    let attempts = 0
    
    while (attempts < MAX_POLL_ATTEMPTS) {
      const task = await audioApi.getTaskStatus(taskId)
      
      if (task.status === 'completed') {
        return {
          text: task.transcription || '',
          segments: []
        }
      }
      
      if (task.status === 'failed') {
        throw new Error(task.error || '转录失败')
      }
      
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL))
      attempts++
    }
    
    throw new Error('转录超时')
  }
}
```

---

### 任务 9：前端集成到解析流程

**Step 1: 修改 TextExtractor.js**

```javascript
// app/src/processors/parse/TextExtractor.js
import { RemoteBackendStrategy } from './RemoteBackendStrategy'
import { AudioTranscriber } from './AudioTranscriber'

export class TextExtractor {
  static strategy = new RemoteBackendStrategy()
  
  static setStrategy(strategy) {
    this.strategy = strategy
  }

  static async extract(filePath, fileType, config = {}) {
    switch (fileType) {
      case 'markdown':
        return await this.extractMarkdown(filePath)
      case 'pdf':
        return await this.extractPdf(filePath, config)
      case 'audio':
        return await this.extractAudio(filePath)
      default:
        throw new Error(`不支持的文件类型: ${fileType}`)
    }
  }

  static async extractMarkdown(filePath) {
    try {
      const result = await window.electronAPI.readMarkdown(filePath)
      return {
        text: result.content || '',
        fileType: 'markdown',
        extractedBy: 'local',
        extractedAt: new Date(),
        wordCount: (result.content || '').split(/\s+/).filter(Boolean).length,
      }
    } catch (error) {
      console.error('Markdown 提取失败:', error)
      throw new Error(`Markdown 提取失败: ${error.message}`)
    }
  }

  static async extractPdf(filePath, config = {}) {
    try {
      return await this.strategy.extractPdf(filePath, config)
    } catch (error) {
      console.error('PDF 提取失败:', error)
      throw this.enhanceError(error)
    }
  }

  static async extractAudio(filePath) {
    const startTime = Date.now()
    const result = await AudioTranscriber.transcribe(filePath)
    const duration = Date.now() - startTime
    
    return {
      text: result.text,
      fileType: 'audio',
      extractedBy: 'siliconflow-asr',
      extractedAt: new Date(),
      wordCount: result.text.split(/\s+/).filter(Boolean).length,
      duration,
    }
  }

  static enhanceError(error) {
    let errorMessage = error.message
    let suggestion = ''

    if (
      errorMessage.includes('A0202') ||
      errorMessage.includes('A0211') ||
      errorMessage.includes('API Key') ||
      errorMessage.includes('API key')
    ) {
      errorMessage = '硅基流动 API Key 无效或已过期'
      suggestion = '请检查配置中的硅基流动 API Key'
    } else if (
      errorMessage.includes('ECONNREFUSED') ||
      errorMessage.includes('network') ||
      errorMessage.includes('ENOTFOUND') ||
      errorMessage.includes('连接')
    ) {
      errorMessage = '无法连接到后端服务'
      suggestion = '请确保后端服务已启动 (cd backend && uv run python -m uvicorn main:app --reload)'
    } else if (errorMessage.includes('Timeout') || errorMessage.includes('超时')) {
      errorMessage = '转录超时'
      suggestion = '请稍后重试，或尝试拆分较大的音频文件'
    } else if (
      errorMessage.includes('format') ||
      errorMessage.includes('损坏') ||
      errorMessage.includes('corrupted')
    ) {
      errorMessage = '音频文件格式不支持或已损坏'
      suggestion = '请尝试使用其他音频文件'
    }

    const fullMessage = suggestion ? `${errorMessage}。${suggestion}` : errorMessage
    return new Error(fullMessage)
  }
}
```

---

### 任务 10：UI 集成

**Step 1: 修改 ParseManagement.vue**

在解析管理页面中添加音频文件的转录支持。由于音频类型已有 `audio` 类型识别，只需确保 parse store 和 UI 能正确处理 `audio` 类型即可（现有架构应该已经支持，因为 parse store 是通用的）。

---

## 测试步骤

### 后端测试
```bash
cd backend
pip install -r requirements.txt
pip install httpx
# 还需要安装 ffmpeg（系统级依赖）
python -m uvicorn main:app --reload
```

### 前端测试
```bash
cd app
npm install
npm run dev
npm run ele
```

### 手动测试步骤
1. 配置硅基流动 API Key
2. 添加音频文件到工作区
3. 在解析管理页面选择音频文件
4. 点击转录，观察状态变化
5. 验证转录结果

---

## 依赖安装

### 后端依赖
```bash
cd backend
pip install httpx
# 还需要安装 ffmpeg（系统级依赖）
```

### 前端依赖
无需新增依赖，使用现有依赖即可。

---

## 架构变更说明

### 为什么移除 IPC？
经检查，项目现有的 PDF 解析架构是：
```
前端 → hook-fetch → FastAPI 后端
```
而非：
```
前端 → Electron IPC → 后端
```

为了保持架构一致性，音频转录采用与 PDF 相同的方式，直接通过 `hook-fetch` 调用后端 API。

### 主要调整点
- ❌ 删除：任务 7（Electron IPC 支持）
- ✅ 新增：任务 7（audioApi 封装，参考 mineruApi）
- ✅ 更新：任务 8（AudioTranscriber 使用 audioApi）
