# 音频解析 API 统一重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 统一音频解析 API 结构，使其与 MinerU API 保持一致的异步任务模式，同时保持音频特色命名。

**架构：** 在现有音频 API 基础上，新增文件上传接口、本地路径接口和结果获取接口，统一使用异步任务模式。

**技术栈：** FastAPI + Pydantic + BackgroundTasks

---

## 前期准备

### Task 0: 查看当前音频 API 完整实现

**Files:**
- Read: `backend/src/api/audio.py`
- Read: `backend/src/audio/task_manager.py`
- Read: `backend/src/models/audio_schemas.py`

**Step 1:** 读取上述文件，了解当前实现细节

---

## 第一阶段：数据模型更新

### Task 1: 更新音频请求 schema

**Files:**
- Modify: `backend/src/models/audio_schemas.py`

**Step 1:** 添加 `LocalAudioTranscriptionRequest` schema

```python
class LocalAudioTranscriptionRequest(BaseModel):
    file_path: str = Field(..., description="音频文件路径")
    model: Optional[str] = Field(None, description="ASR 模型名称（可选）")
```

**Step 2:** 确认现有 `AudioTranscriptionRequest` 保持不变（用于向后兼容）

**Step 3:** 提交

```bash
git add backend/src/models/audio_schemas.py
git commit -m "feat: add LocalAudioTranscriptionRequest schema"
```

---

### Task 2: 更新音频响应 schema（如需要）

**Files:**
- Modify: `backend/src/models/audio_schemas.py`（如需要）

**Step 1:** 检查当前响应是否满足需求

**Step 2:** 如需调整则修改，否则跳过

---

## 第二阶段：API 端点实现

### Task 3: 新增 `/transcribe` 端点（文件上传）

**Files:**
- Modify: `backend/src/api/audio.py`

**Step 1:** 添加必要的导入

```python
from fastapi import UploadFile, File, BackgroundTasks
import aiofiles
from pathlib import Path
```

**Step 2:** 实现 `/transcribe` 端点

```python
@router.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: Optional[str] = None,
):
    """上传音频文件并创建转录任务"""
    try:
        # 保存上传的文件到临时位置
        import tempfile
        import os
        
        suffix = Path(file.filename).suffix if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_file_path = tmp.name
        
        logger.info(f"收到音频上传: {file.filename}, 临时路径: {temp_file_path}")

        # 创建任务
        result = await audio_processor.process(
            temp_file_path,
            config={"model": model} if model else None,
        )

        # 注意：临时文件清理需要在任务完成后处理
        # 这里简化处理，实际使用时需要考虑更好的清理策略

        return AudioTranscriptionResponse(**result)

    except Exception as e:
        logger.error(f"音频上传转录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3:** 注意：需要与现有 `/transcribe` 端点区分开，或者重命名现有端点

**建议方案：**
- 现有 `/transcribe` 重命名为 `/transcribe-local`
- 新的文件上传端点使用 `/transcribe`

**Step 4:** 提交

```bash
git add backend/src/api/audio.py
git commit -m "feat: add audio upload endpoint"
```

---

### Task 4: 重命名现有端点为 `/transcribe-local`

**Files:**
- Modify: `backend/src/api/audio.py`

**Step 1:** 将现有的 `transcribe_audio` 函数重命名为 `transcribe_audio_local`

**Step 2:** 将路由从 `/transcribe` 改为 `/transcribe-local`

**Step 3:** 更新请求参数使用 `LocalAudioTranscriptionRequest`

```python
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
```

**Step 4:** 保留原有 `/transcribe` 作为别名（可选，用于向后兼容）

**Step 5:** 提交

```bash
git add backend/src/api/audio.py
git commit -m "feat: rename transcribe endpoint to transcribe-local"
```

---

### Task 5: 新增 `/tasks/{task_id}/result` 端点

**Files:**
- Modify: `backend/src/api/audio.py`

**Step 1:** 实现结果获取端点

```python
@router.get("/tasks/{task_id}/result")
async def get_transcription_result(task_id: str):
    """获取转录结果"""
    task = audio_task_manager.get_task(task_id)
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
```

**Step 2:** 提交

```bash
git add backend/src/api/audio.py
git commit -m "feat: add transcription result endpoint"
```

---

## 第三阶段：增强任务管理器（可选）

### Task 6: 增强 AudioTaskManager（如需要）

**Files:**
- Read: `backend/src/audio/task_manager.py`

**Step 1:** 检查当前任务管理器是否满足需求

**Step 2:** 如需增强则修改，否则跳过

---

## 第四阶段：前端 API 更新（可选）

### Task 7: 更新前端 backend.js

**Files:**
- Modify: `app/src/utils/backend.js`

**Step 1:** 更新 AudioApi 类

```javascript
class AudioApi {
  constructor(backendService) {
    this.backend = backendService
  }

  async transcribeAudioUpload(file, config = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (config.model) {
      formData.append('model', config.model)
    }
    
    const request = this.backend.client.post('/api/audio/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return await request.json()
  }

  async transcribeAudioLocal(filePath, config = {}) {
    const request = this.backend.client.post('/api/audio/transcribe-local', {
      file_path: filePath,
      model: config.model,
    })
    return await request.json()
  }

  async getTaskStatus(taskId) {
    const request = this.backend.client.get(`/api/audio/tasks/${taskId}`)
    return await request.json()
  }

  async getTaskResult(taskId) {
    const request = this.backend.client.get(`/api/audio/tasks/${taskId}/result`)
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
```

**Step 2:** 保持向后兼容 - 保留原有的 `transcribeAudio` 方法作为 `transcribeAudioLocal` 的别名

**Step 3:** 提交

```bash
git add app/src/utils/backend.js
git commit -m "feat: update frontend audio API client"
```

---

## 第五阶段：验证与测试

### Task 8: 运行后端测试（如有）

**Step 1:** 检查是否有后端测试

**Step 2:** 运行测试（如有）

---

### Task 9: 更新 API 文档（可选）

**Files:**
- Update: 相关文档（如需要）

---

## 总结

### 文件变更总览

**后端：**
- `backend/src/models/audio_schemas.py` - 添加 LocalAudioTranscriptionRequest
- `backend/src/api/audio.py` - 新增/重命名端点，添加 result 端点

**前端（可选）：**
- `app/src/utils/backend.js` - 更新 AudioApi 客户端

### API 端点最终列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/audio/transcribe` | POST | 上传音频文件，创建转录任务 |
| `/api/audio/transcribe-local` | POST | 本地文件路径，创建转录任务 |
| `/api/audio/tasks/{task_id}` | GET | 获取任务状态 |
| `/api/audio/tasks/{task_id}/result` | GET | 获取转录结果 |
| `/api/audio/tasks` | GET | 列出所有任务 |
| `/api/audio/tasks/{task_id}` | DELETE | 删除任务 |

---

**Plan complete and saved to `docs/plans/2026-03-03-audio-api-unification.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
