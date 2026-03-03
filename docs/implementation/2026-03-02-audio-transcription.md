# 音频转录功能实施报告

**日期**: 2026-03-02  
**版本**: v1.0  
**状态**: ✅ 已完成

## 概述

实现了基于硅基流动 API 的音频文件转录功能，支持大文件分块处理，采用插件化架构设计。

## 完成的工作

### 后端部分

#### 1. 配置和数据模型
- **文件**: `backend/src/config.py`
  - 添加硅基流动配置项（API Key、Base URL、ASR 模型）
  - 添加音频分块配置（分块时长、最大文件大小）

- **文件**: `backend/src/models/audio_schemas.py`
  - `AudioTaskStatus`: 任务状态枚举（pending, processing, chunking, transcribing, merging, completed, failed）
  - `AudioTranscriptionRequest`: 转录请求模型
  - `AudioChunkInfo`: 音频分块信息模型
  - `AudioTaskInfo`: 音频任务信息模型
  - `AudioTranscriptionResponse`: 转录响应模型

#### 2. ASR 提供商抽象层
- **文件**: `backend/src/audio/providers/base.py`
  - `ASRProvider` 抽象基类，定义 `transcribe()` 和 `validate_config()` 接口

- **文件**: `backend/src/audio/providers/siliconflow.py`
  - `SiliconFlowASRProvider` 实现类
  - 使用 httpx 异步客户端调用硅基流动 API
  - 支持自定义 API Key、Base URL 和模型

#### 3. 音频分块处理
- **文件**: `backend/src/audio/chunker.py`
  - `AudioChunker` 类，使用 ffmpeg 进行音频分块
  - `get_audio_duration()`: 获取音频时长
  - `chunk_audio()`: 执行分块操作
  - `cleanup_chunks()`: 清理分块文件

- **文件**: `backend/src/audio/utils.py`
  - `SUPPORTED_AUDIO_EXTENSIONS`: 支持的音频格式集合
  - `is_audio_file()`: 判断是否为音频文件
  - `merge_transcriptions()`: 合并多块转录文本

#### 4. FileProcessor 抽象层
- **文件**: `backend/src/processors/base.py`
  - `FileProcessor` 抽象基类，定义 `process()` 和 `supports()` 接口

- **文件**: `backend/src/processors/audio_processor.py`
  - `AudioProcessor` 实现类
  - 后台任务处理，不阻塞请求
  - 分块 → 逐块转录 → 合并结果 → 清理文件

#### 5. 任务管理器
- **文件**: `backend/src/audio/task_manager.py`
  - `AudioTaskManager` 单例类
  - 内存存储任务状态
  - 线程安全的任务增删改查

#### 6. FastAPI 路由
- **文件**: `backend/src/api/audio.py`
  - `POST /api/audio/transcribe`: 创建转录任务
  - `GET /api/audio/tasks/{task_id}`: 获取任务状态
  - `GET /api/audio/tasks`: 列出所有任务
  - `DELETE /api/audio/tasks/{task_id}`: 删除任务

- **文件**: `backend/main.py`
  - 注册音频路由

### 前端部分

#### 7. API 封装
- **文件**: `app/src/utils/backend.js`
  - `AudioApi` 类
  - `transcribeAudio()`: 创建转录任务
  - `getTaskStatus()`: 查询任务状态
  - `listTasks()`: 列出任务
  - `deleteTask()`: 删除任务

#### 8. AudioTranscriber 实现
- **文件**: `app/src/processors/parse/AudioTranscriber.js`
  - `transcribe()`: 主转录方法
  - `_pollTask()`: 轮询任务状态直至完成
  - 从 agent store 获取硅基流动配置

#### 9. 解析流程集成
- **文件**: `app/src/processors/parse/TextExtractor.js`
  - 添加 `extractAudio()` 方法
  - 修改 `enhanceError()` 支持 `fileType` 参数
  - 区分 PDF 和音频的错误提示

#### 10. UI 集成
- 现有架构已支持，无需额外修改
- `document store` 已包含音频文件类型识别
- `parse store` 通用设计自动支持音频类型

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                        │
├─────────────────────────────────────────────────────────────┤
│  ParseManagement  │  TextExtractor  │  AudioTranscriber    │
└────────────────┬────────────────────────────────────────────┘
                 │ hook-fetch (HTTP)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│  /api/audio/*  │  AudioProcessor  │  AudioTaskManager     │
├─────────────────────────────────────────────────────────────┤
│  AudioChunker  │  SiliconFlowASRProvider  │  (ffmpeg)       │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   硅基流动 ASR API                           │
│           FunAudioLLM/SenseVoiceSmall                        │
└─────────────────────────────────────────────────────────────┘
```

## 文件清单

### 新增文件
```
backend/
├── src/
│   ├── models/
│   │   └── audio_schemas.py
│   ├── audio/
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── siliconflow.py
│   │   │   └── __init__.py
│   │   ├── chunker.py
│   │   ├── utils.py
│   │   └── task_manager.py
│   ├── processors/
│   │   ├── base.py
│   │   ├── audio_processor.py
│   │   └── __init__.py
│   └── api/
│       └── audio.py
app/
└── src/
    ├── utils/
    │   └── backend.js (修改)
    └── processors/parse/
        ├── AudioTranscriber.js (重写)
        └── TextExtractor.js (修改)
```

### 修改文件
- `backend/src/config.py`
- `backend/src/models/__init__.py`
- `backend/main.py`
- `app/src/utils/backend.js`
- `app/src/processors/parse/AudioTranscriber.js`
- `app/src/processors/parse/TextExtractor.js`

## 依赖项

### 后端
- `httpx`: 异步 HTTP 客户端
- `ffmpeg`: 系统级依赖，用于音频分块

### 前端
- 无新增依赖，使用现有依赖

## 测试建议

1. **后端启动**
```bash
cd backend
pip install httpx
python -m uvicorn main:app --reload
```

2. **前端启动**
```bash
cd app
npm install
npm run dev
npm run ele
```

3. **手动测试步骤**
   - 在设置中配置硅基流动 API Key
   - 添加音频文件到工作区
   - 在解析管理页面选择音频文件
   - 点击转录，观察状态变化
   - 验证转录结果

## 已知问题

无

## 后续优化建议

1. 任务持久化：当前任务存储在内存中，重启后丢失，可考虑持久化到数据库
2. 并发控制：限制同时处理的任务数量
3. 进度反馈：更细粒度的进度百分比
4. 更多 ASR 提供商：添加 OpenAI Whisper、阿里云等支持

---

**实施人**: AI Assistant  
**审核人**: -
