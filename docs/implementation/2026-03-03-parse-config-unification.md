# 解析配置统一重构实施报告

**日期：** 2026-03-03  
**版本：** v1.0  
**状态：** ✅ 已完成

## 概述

本次重构将音频解析和文档解析的敏感配置（API Key、Base URL）统一改为由后端环境变量管理，前端仅保留用户偏好设置（服务提供商选择、模型选择等），实现了配置管理的职责分离和安全性提升。

## 目标

1. **安全性提升**：敏感配置不再通过前端传递或存储
2. **架构统一**：音频解析和文档解析使用相同的配置管理模式
3. **用户体验**：保留前端用户偏好设置的灵活性
4. **扩展性**：为未来添加多种解析服务提供商预留架构

## 实现内容

### 1. 后端改动

#### 环境变量配置更新

**文件：** `backend/.env.example`

新增硅基流动（SiliconFlow）音频解析配置：

```env
# 硅基流动 API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_API_BASE_URL=https://api.siliconflow.cn
SILICONFLOW_ASR_MODEL=FunAudioLLM/SenseVoiceSmall

# 音频分块配置
AUDIO_CHUNK_DURATION_MINUTES=50
AUDIO_MAX_FILE_SIZE_MB=50
```

#### 音频 API 简化

**文件：** `backend/src/models/audio_schemas.py`

- 移除 `AudioTranscriptionRequest` 中的 `api_key` 和 `base_url` 字段
- 新增 `LocalAudioTranscriptionRequest` schema（用于本地路径解析）

**文件：** `backend/src/api/audio.py`

- 简化 `transcribe_audio` 函数，移除前端配置传递
- 音频处理器从 `settings` 读取配置，而非前端传入

**文件：** `backend/src/processors/audio_processor.py`

- 导入 `settings` 配置
- `SiliconFlowASRProvider` 使用后端环境变量配置
- 优先使用传入的 model（可选），否则使用默认值

### 2. 前端改动

#### 新增 parseConfig store

**文件：** `app/src/stores/parseConfig.js`

独立的解析配置 store，管理用户偏好设置：

```javascript
{
  audioConfig: {
    provider: 'siliconflow',      // 服务提供商选择
    asrModel: 'FunAudioLLM/SenseVoiceSmall',  // ASR 模型选择
  },
  docParseConfig: {
    provider: 'mineru',           // 服务提供商选择
    enableFormula: true,          // 启用公式识别
    enableTable: true,            // 启用表格识别
    enableOcr: true,              // 启用 OCR
    language: 'auto',             // 语言设置
  }
}
```

**持久化：** Pinia persist，key: `qbase-parse-config`

#### 清理 agent store

**文件：** `app/src/stores/agent.js`

- 从 `llmConfig` 中移除 `mineru` 和 `siliconflow` 配置对象
- 保持 LLM 配置独立

#### 新增音频解析设置组件

**文件：** `app/src/components/settings/AudioParseSettings.vue`

新建设置页面组件：
- 服务提供商选择下拉框
- ASR 模型选择输入框
- 提示信息：敏感配置在后端 `.env` 文件中设置

#### 更新 PDF 解析设置组件

**文件：** `app/src/components/settings/PdfParseSettings.vue`

- 移除 API Key 和 Base URL 输入框
- 保留高级选项（公式、表格、OCR、语言）
- 使用 `parseConfigStore` 而非 `agentStore`
- 添加提示信息

#### 更新音频转录器

**文件：** `app/src/processors/parse/AudioTranscriber.js`

- 从 `useParseConfigStore` 读取配置
- 调用后端 API 时只传 model 参数

#### 更新后端 API 客户端

**文件：** `app/src/utils/backend.js`

- 简化 `AudioApi.transcribeAudio()` 方法
- 移除 `apiKey` 和 `baseUrl` 参数传递

#### 集成设置页面

**文件：** 
- `app/src/views/Settings.vue`
- `app/src/components/Layout/SettingsSidebar.vue`

- 新增"音频解析"菜单项
- 集成 `AudioParseSettings` 组件

## API 对比

### 改动前

```javascript
// 前端
const result = await audioApi.transcribeAudio(filePath, {
  apiKey: 'sk-xxx',        // 敏感信息在前端
  baseUrl: 'https://...',   // 敏感信息在前端
  model: 'FunAudioLLM/...'
})
```

### 改动后

```javascript
// 前端
const result = await audioApi.transcribeAudio(filePath, {
  model: 'FunAudioLLM/...'  // 仅用户偏好
})

// 后端从环境变量读取
// SILICONFLOW_API_KEY, SILICONFLOW_API_BASE_URL
```

## 配置管理架构

### 职责分离

| 层级 | 内容 | 存储位置 |
|------|------|---------|
| **后端配置** | API Key, Base URL | 环境变量 (.env) |
| **用户偏好** | Provider, Model, Options | LocalStorage (Pinia) |

### 配置优先级

**音频解析：**
1. 前端传入的 model（可选）
2. 后端环境变量 `SILICONFLOW_ASR_MODEL`
3. 代码默认值

**文档解析：**
1. 前端传入的选项（enableFormula, enableTable 等）
2. 后端环境变量 `MINERU_API_KEY`, `MINERU_API_BASE_URL`

## 文件变更清单

### 后端文件
- `backend/.env.example` - 添加硅基流动配置示例
- `backend/src/models/audio_schemas.py` - 简化请求 schema
- `backend/src/api/audio.py` - 简化 API，移除敏感参数
- `backend/src/processors/audio_processor.py` - 使用后端配置

### 前端文件
- `app/src/stores/parseConfig.js` - 新增配置 store
- `app/src/stores/agent.js` - 清理旧配置
- `app/src/components/settings/AudioParseSettings.vue` - 新增
- `app/src/components/settings/PdfParseSettings.vue` - 更新
- `app/src/processors/parse/AudioTranscriber.js` - 更新
- `app/src/utils/backend.js` - 简化 API 调用
- `app/src/views/Settings.vue` - 集成新组件
- `app/src/components/Layout/SettingsSidebar.vue` - 添加菜单项

## 验证结果

### 前端构建检查

✅ 运行 `npm run build` 通过  
✅ 所有组件正确导入和使用  
✅ 无 TypeScript 错误

### Git 提交历史

```
feat: add parseConfig store for user preferences
refactor: remove mineru/siliconflow from agent store
feat: add AudioParseSettings component
refactor: update PdfParseSettings to use parseConfig store
refactor: update AudioTranscriber to use parseConfig store
refactor: simplify backend API parameters
feat: integrate new parse settings components
```

## 优势总结

1. **安全性提升**
   - 敏感配置不再在前端传递或存储
   - 避免 API Key 泄露风险

2. **架构清晰**
   - 职责分离明确
   - 配置管理集中化

3. **用户体验保持**
   - 前端仍可选择模型和选项
   - 设置界面友好提示

4. **扩展性增强**
   - 为未来添加多种解析服务预留架构
   - Provider 选择器已就绪

## 相关文档

- [设计文档](../plans/2026-03-03-parse-config-unification-design.md)
- [实施计划](../plans/2026-03-03-parse-config-unification.md)
