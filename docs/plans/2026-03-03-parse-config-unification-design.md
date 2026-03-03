# 解析配置统一重构设计方案

**日期：** 2026-03-03
**版本：** v1.0

## 一、概述

将音频解析和文档解析的敏感配置（API Key、Base URL）统一改为由后端环境变量管理，前端保留服务提供商选择和模型选择等用户偏好设置。

## 二、目标

- 音频解析 API Key 等敏感配置完全由后端环境变量管理
- 前端保留服务提供商选择和模型选择等用户偏好设置
- 明确区分"后端服务配置（环境变量）"和"用户偏好设置"
- 为未来扩展多种解析服务预留架构

## 三、后端改动

### 3.1 环境变量配置

**文件：** `backend/.env.example`

添加硅基流动配置：
```env
# MinerU API 配置
MINERU_API_KEY=your_mineru_api_key_here
MINERU_API_BASE_URL=https://mineru.net

# 硅基流动 API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_API_BASE_URL=https://api.siliconflow.cn
SILICONFLOW_ASR_MODEL=FunAudioLLM/SenseVoiceSmall

# 音频分块配置
AUDIO_CHUNK_DURATION_MINUTES=50
AUDIO_MAX_FILE_SIZE_MB=50

# 存储目录配置
STORAGE_DIR=./storage

# 任务轮询配置
TASK_POLL_INTERVAL=3
MAX_POLL_ATTEMPTS=60
```

### 3.2 音频 API 简化

**文件：** `backend/src/api/audio.py`

- 移除 `api_key`, `base_url` 请求参数
- 只保留 `file_path` 和可选的 `model`

### 3.3 MinerU API 增强

**文件：** `backend/src/api/mineru.py`

- 接受前端传入的配置选项（enableFormula, enableTable 等）
- API Key/Base URL 仍从环境变量读取

## 四、前端改动

### 4.1 新增 Store

**文件：** `app/src/stores/parse.js`

独立的解析配置 store，包含：
- `audioConfig`: 音频解析配置（provider, asrModel）
- `docParseConfig`: 文档解析配置（provider, enableFormula, enableTable, enableOcr, language）

### 4.2 现有 Store 清理

**文件：** `app/src/stores/agent.js`

从 `llmConfig` 中移除 `mineru` 和 `siliconflow` 对象

### 4.3 新增设置组件

**文件：** `app/src/components/settings/AudioParseSettings.vue`

- 音频解析服务提供商选择
- ASR 模型选择
- 提示信息：API Key 等敏感配置需在后端 `.env` 文件中设置

### 4.4 修改 PDF 解析设置

**文件：** `app/src/components/settings/PdfParseSettings.vue`

- 移除 API Key 和 Base URL 输入框
- 保留高级选项（公式、表格、OCR、语言）
- 添加提示信息

### 4.5 更新 AudioTranscriber

**文件：** `app/src/processors/parse/AudioTranscriber.js`

- 从 `parseStore` 读取配置
- 调用后端 API 时只传 `model`（可选）

### 4.6 更新 backend.js

**文件：** `app/src/utils/backend.js`

- `AudioApi.transcribeAudio()` 参数简化
- `MinerUApi` 增强，支持传递配置选项

## 五、数据流程图

```
前端用户操作
    ↓
parseStore (用户偏好：provider + model)
    ↓
AudioTranscriber / TextExtractor
    ↓
backend.js API (仅传用户选择，不传密钥)
    ↓
后端 FastAPI
    ↓
后端 config.py (从环境变量读取 API Key)
    ↓
第三方服务 API
```

## 六、文件变更清单

### 后端文件
- `backend/.env.example` - 添加硅基流动配置示例
- `backend/src/api/audio.py` - 简化请求参数
- `backend/src/processors/audio_processor.py` - 移除前端配置传递
- `backend/src/api/mineru.py` - 增强接受前端配置选项

### 前端文件
- `app/src/stores/parse.js` - 新增解析配置 store
- `app/src/stores/agent.js` - 移除 mineru/siliconflow 配置
- `app/src/components/settings/AudioParseSettings.vue` - 新增音频解析设置
- `app/src/components/settings/PdfParseSettings.vue` - 修改 PDF 解析设置
- `app/src/processors/parse/AudioTranscriber.js` - 更新配置来源
- `app/src/utils/backend.js` - 简化 API 参数
- 设置页面入口 - 集成新的设置组件
