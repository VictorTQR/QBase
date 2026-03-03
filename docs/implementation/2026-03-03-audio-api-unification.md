# 音频 API 统一重构实施报告

**日期：** 2026-03-03  
**版本：** v1.0  
**状态：** ✅ 已完成

## 概述

本次重构统一了音频解析 API 结构，使其与 MinerU 文档解析 API 保持一致的异步任务模式，同时保持音频特色命名。新增了文件上传接口、本地路径接口和结果获取接口，提升了 API 的一致性和可用性。

## 目标

1. **API 一致性**：音频解析与文档解析使用相同的接口模式
2. **功能增强**：提供文件上传和本地路径两种解析方式
3. **向后兼容**：保留原有接口作为别名，不破坏现有功能
4. **用户体验**：提供专门的结果获取端点

## 实现内容

### 1. 后端 API 端点

#### 新增端点

**POST /api/audio/transcribe-upload**

上传音频文件并创建转录任务：

```python
@router.post("/transcribe-upload", response_model=AudioTranscriptionResponse)
async def transcribe_audio_upload(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
):
    """上传音频文件并创建转录任务"""
```

**功能：**
- 接收 multipart/form-data 格式的文件上传
- 可选的 model 参数（Form 格式）
- 文件保存到临时目录
- 创建异步转录任务
- 返回任务 ID 和状态

---

**POST /api/audio/transcribe-local**

通过本地文件路径创建转录任务：

```python
@router.post("/transcribe-local", response_model=AudioTranscriptionResponse)
async def transcribe_audio_local(request: LocalAudioTranscriptionRequest):
    """通过本地文件路径创建音频转录任务"""
```

**功能：**
- 接收 JSON 格式的本地文件路径
- 可选的 model 参数
- 创建异步转录任务
- 返回任务 ID 和状态

---

**GET /api/audio/tasks/{task_id}/result**

获取转录结果：

```python
@router.get("/tasks/{task_id}/result")
async def get_transcription_result(task_id: str):
    """获取转录结果"""
```

**功能：**
- 验证任务是否存在
- 验证任务是否已完成
- 返回完整的转录结果（文本、元数据等）

**响应格式：**
```json
{
  "task_id": "xxx",
  "transcription": "完整的转录文本",
  "file_name": "audio.mp3",
  "total_duration": 120.5,
  "total_size": 1024000,
  "created_at": 1234567890.123,
  "completed_at": 1234567900.123
}
```

#### 保留端点（向后兼容）

**POST /api/audio/transcribe**

保留为向后兼容别名，等同于 `/transcribe-local`。

#### 现有端点（保持不变）

- `GET /api/audio/tasks/{task_id}` - 获取任务状态
- `GET /api/audio/tasks` - 列出所有任务
- `DELETE /api/audio/tasks/{task_id}` - 删除任务

### 2. 数据模型更新

**文件：** `backend/src/models/audio_schemas.py`

新增 `LocalAudioTranscriptionRequest` schema：

```python
class LocalAudioTranscriptionRequest(BaseModel):
    file_path: str = Field(..., description="音频文件路径")
    model: Optional[str] = Field(None, description="ASR 模型名称（可选）")
```

### 3. 前端 API 客户端更新

**文件：** `app/src/utils/backend.js`

#### 新增方法

**transcribeAudioUpload(file, config)**

```javascript
async transcribeAudioUpload(file, config = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (config.model) {
    formData.append('model', config.model)
  }
  
  const request = this.backend.client.post('/api/audio/transcribe-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return await request.json()
}
```

**transcribeAudioLocal(filePath, config)**

```javascript
async transcribeAudioLocal(filePath, config = {}) {
  const request = this.backend.client.post('/api/audio/transcribe-local', {
    file_path: filePath,
    model: config.model,
  })
  return await request.json()
}
```

**getTaskResult(taskId)**

```javascript
async getTaskResult(taskId) {
  const request = this.backend.client.get(`/api/audio/tasks/${taskId}/result`)
  return await request.json()
}
```

#### 保留方法（向后兼容）

- `transcribeAudio(filePath, config)` - 保留为 `transcribeAudioLocal` 的别名

## API 端点完整列表

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/audio/transcribe-upload` | POST | 上传音频文件，创建转录任务 | ✅ 新增 |
| `/api/audio/transcribe-local` | POST | 本地文件路径，创建转录任务 | ✅ 新增 |
| `/api/audio/transcribe` | POST | 向后兼容别名 | ✅ 保留 |
| `/api/audio/tasks/{task_id}` | GET | 获取任务状态 | ✅ 现有 |
| `/api/audio/tasks/{task_id}/result` | GET | 获取转录结果 | ✅ 新增 |
| `/api/audio/tasks` | GET | 列出所有任务 | ✅ 现有 |
| `/api/audio/tasks/{task_id}` | DELETE | 删除任务 | ✅ 现有 |

## 使用示例

### 上传文件转录

```javascript
import { audioApi } from '@/utils/backend'

// 1. 上传文件并创建任务
const result = await audioApi.transcribeAudioUpload(file, {
  model: 'FunAudioLLM/SenseVoiceSmall'
})
const taskId = result.task_id

// 2. 轮询任务状态
while (true) {
  const task = await audioApi.getTaskStatus(taskId)
  if (task.status === 'completed') {
    // 3. 获取完整结果
    const finalResult = await audioApi.getTaskResult(taskId)
    console.log('转录完成:', finalResult.transcription)
    break
  }
  if (task.status === 'failed') {
    throw new Error(task.error)
  }
  await new Promise(r => setTimeout(r, 3000))
}
```

### 本地文件转录

```javascript
import { audioApi } from '@/utils/backend'

// 1. 使用本地路径创建任务
const result = await audioApi.transcribeAudioLocal(
  '/path/to/audio.mp3',
  { model: 'FunAudioLLM/SenseVoiceSmall' }
)
const taskId = result.task_id

// 2. 获取结果（方式同上）
```

## 与 MinerU API 对比

| 功能 | MinerU API | 音频 API | 一致性 |
|------|-----------|---------|--------|
| 文件上传 | `/parse` | `/transcribe-upload` | ✅ 模式一致 |
| 本地路径 | `/parse-local` | `/transcribe-local` | ✅ 命名一致 |
| 任务状态 | `/tasks/{task_id}` | `/tasks/{task_id}` | ✅ 完全一致 |
| 获取结果 | `/tasks/{task_id}/result` | `/tasks/{task_id}/result` | ✅ 完全一致 |
| 下载文件 | `/tasks/{task_id}/download` | - | 音频无需下载 |

## 文件变更清单

### 后端文件
- `backend/src/models/audio_schemas.py` - 新增 LocalAudioTranscriptionRequest
- `backend/src/api/audio.py` - 新增/重命名端点，添加 result 端点

### 前端文件
- `app/src/utils/backend.js` - 新增 transcribeAudioUpload、transcribeAudioLocal、getTaskResult

## 验证结果

### 前端构建检查

✅ 运行 `npm run build` 通过  
✅ 所有 API 方法正确定义  
✅ 无 TypeScript 错误

### Git 提交历史

```
feat: unify audio API structure with upload, local, and result endpoints
feat: update frontend audio API client with new endpoints
```

## 优势总结

1. **API 一致性**
   - 与 MinerU API 保持相同的异步任务模式
   - 命名规范统一（transcribe vs parse）
   - 端点结构一致

2. **功能增强**
   - 支持文件上传和本地路径两种方式
   - 专门的结果获取端点
   - 更清晰的 API 职责划分

3. **向后兼容**
   - 保留原有 `/transcribe` 端点
   - 现有代码无需修改即可继续工作

4. **扩展性**
   - 为未来添加更多音频处理功能预留空间
   - 统一的任务管理模式

## 相关文档

- [实施计划](../plans/2026-03-03-audio-api-unification.md)
- [解析配置统一实施报告](./2026-03-03-parse-config-unification.md)
