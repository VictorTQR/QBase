# 解析配置统一重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 将音频解析和文档解析的敏感配置统一改为由后端环境变量管理，前端保留用户偏好设置。

**架构：** 新增独立的 parse store 管理用户偏好，后端从环境变量读取敏感配置，前后端 API 简化参数传递。

**技术栈：** Vue 3 + Pinia + FastAPI + Pydantic Settings

---

## 前期准备

### Task 0: 查看相关文件结构

**Files:**
- Read: `app/src/components/Settings.vue`（找到设置页面入口）

**Step 1:** 读取 Settings.vue 了解现有设置页面结构

---

## 第一阶段：后端改动

### Task 1: 更新后端环境变量示例

**Files:**
- Modify: `backend/.env.example`

**Step 1:** 在 `.env.example` 中添加硅基流动配置

```env
# 硅基流动 API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_API_BASE_URL=https://api.siliconflow.cn
SILICONFLOW_ASR_MODEL=FunAudioLLM/SenseVoiceSmall

# 音频分块配置
AUDIO_CHUNK_DURATION_MINUTES=50
AUDIO_MAX_FILE_SIZE_MB=50
```

**Step 2:** 确认 config.py 已有这些配置项（应该已有）

**Step 3:** 提交

```bash
git add backend/.env.example
git commit -m "docs: add siliconflow config to .env.example"
```

---

### Task 2: 修改后端音频 API - 简化请求参数

**Files:**
- Read: `backend/src/models/audio_schemas.py`
- Modify: `backend/src/api/audio.py`
- Modify: `backend/src/processors/audio_processor.py`

**Step 1:** 查看当前 AudioTranscriptionRequest schema 定义

**Step 2:** 修改 audio_schemas.py - 移除 api_key 和 base_url 字段

```python
class AudioTranscriptionRequest(BaseModel):
    file_path: str
    model: Optional[str] = None  # 可选，覆盖默认模型
```

**Step 3:** 修改 audio.py - 简化 transcribe_audio 函数

```python
@router.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(request: AudioTranscriptionRequest):
    """创建音频转录任务"""
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

**Step 4:** 修改 audio_processor.py - process 方法只接受可选的 model

**Step 5:** 提交

```bash
git add backend/src/models/audio_schemas.py backend/src/api/audio.py backend/src/processors/audio_processor.py
git commit -m "refactor: simplify audio API, use env vars for credentials"
```

---

### Task 3: 增强后端 MinerU API - 接受前端配置选项

**Files:**
- Read: `backend/src/api/mineru.py`
- Read: `backend/src/mineru/client.py`

**Step 1:** 查看当前 MinerU API 定义

**Step 2:** 修改 mineru.py - 添加接受配置选项的参数

**Step 3:** 修改 client.py - 支持传入配置选项

**Step 4:** 提交

```bash
git add backend/src/api/mineru.py backend/src/mineru/client.py
git commit -m "feat: allow mineru API to accept frontend config options"
```

---

## 第二阶段：前端改动

### Task 4: 新增 parse store

**Files:**
- Create: `app/src/stores/parse.js`

**Step 1:** 创建 parse.js 文件

```javascript
import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useParseStore = defineStore(
  'parse',
  () => {
    const audioConfig = ref({
      provider: 'siliconflow',
      asrModel: 'FunAudioLLM/SenseVoiceSmall',
    })

    const docParseConfig = ref({
      provider: 'mineru',
      enableFormula: true,
      enableTable: true,
      enableOcr: true,
      language: 'auto',
    })

    function setAudioConfig(config) {
      audioConfig.value = { ...audioConfig.value, ...config }
    }

    function setDocParseConfig(config) {
      docParseConfig.value = { ...docParseConfig.value, ...config }
    }

    return {
      audioConfig,
      docParseConfig,
      setAudioConfig,
      setDocParseConfig,
    }
  },
  {
    persist: {
      key: 'qbase-parse-config',
    },
  },
)
```

**Step 2:** 提交

```bash
git add app/src/stores/parse.js
git commit -m "feat: add parse store for user preferences"
```

---

### Task 5: 清理 agent store - 移除 mineru/siliconflow 配置

**Files:**
- Modify: `app/src/stores/agent.js`

**Step 1:** 从 llmConfig 中移除 mineru 和 siliconflow

```javascript
const llmConfig = ref({
  type: 'openai',
  baseUrl: 'https://api.openai.com/v1',
  apiKey: '',
  model: 'gpt-3.5-turbo',
})
```

**Step 2:** 提交

```bash
git add app/src/stores/agent.js
git commit -m "refactor: remove mineru/siliconflow from agent store"
```

---

### Task 6: 新增 AudioParseSettings.vue 组件

**Files:**
- Create: `app/src/components/settings/AudioParseSettings.vue`

**Step 1:** 创建组件文件

```vue
<template>
  <div class="audio-parse-settings">
    <el-form label-width="140px">
      <el-divider content-position="left">音频解析配置</el-divider>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        API Key 和 Base URL 等敏感配置需在后端
        <code>.env</code> 文件中设置
      </el-alert>

      <el-form-item label="服务提供商">
        <el-select v-model="audioConfig.provider" style="width: 200px">
          <el-option label="硅基流动" value="siliconflow" />
        </el-select>
      </el-form-item>

      <el-form-item label="ASR 模型">
        <el-input v-model="audioConfig.asrModel" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useParseStore } from '@/stores/parse'

const parseStore = useParseStore()
const isUpdating = ref(false)

const audioConfig = ref({
  provider: 'siliconflow',
  asrModel: 'FunAudioLLM/SenseVoiceSmall',
})

watch(
  () => parseStore.audioConfig,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    audioConfig.value = { ...config }
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { immediate: true, deep: true },
)

watch(
  audioConfig,
  (newConfig) => {
    if (isUpdating.value) return
    isUpdating.value = true
    parseStore.setAudioConfig({ ...newConfig })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)
</script>

<style scoped>
.audio-parse-settings {
  padding: 8px 0;
}
</style>
```

**Step 2:** 提交

```bash
git add app/src/components/settings/AudioParseSettings.vue
git commit -m "feat: add AudioParseSettings component"
```

---

### Task 7: 修改 PdfParseSettings.vue 组件

**Files:**
- Modify: `app/src/components/settings/PdfParseSettings.vue`

**Step 1:** 移除 API Key 和 Base URL 输入框

**Step 2:** 添加提示信息

**Step 3:** 从 parseStore 读取配置，而不是 agentStore

**Step 4:** 提交

```bash
git add app/src/components/settings/PdfParseSettings.vue
git commit -m "refactor: update PdfParseSettings to use parse store"
```

---

### Task 8: 更新 AudioTranscriber.js

**Files:**
- Modify: `app/src/processors/parse/AudioTranscriber.js`

**Step 1:** 从 useParseStore 读取配置，而不是 useAgentStore

**Step 2:** 调用 audioApi.transcribeAudio 时只传 model

```javascript
import { useParseStore } from '@/stores/parse'
import { audioApi } from '@/utils/backend'

const POLL_INTERVAL = 3000
const MAX_POLL_ATTEMPTS = 600

export class AudioTranscriber {
  static async transcribe(filePath) {
    const parseStore = useParseStore()
    const { asrModel } = parseStore.audioConfig
    
    try {
      const result = await audioApi.transcribeAudio(filePath, { model: asrModel })
      return await this._pollTask(result.task_id)
    } catch (error) {
      console.error('音频转录失败:', error)
      throw error
    }
  }
  
  // ... _pollTask 方法保持不变
}
```

**Step 3:** 提交

```bash
git add app/src/processors/parse/AudioTranscriber.js
git commit -m "refactor: update AudioTranscriber to use parse store"
```

---

### Task 9: 更新 backend.js - 简化 API 参数

**Files:**
- Modify: `app/src/utils/backend.js`

**Step 1:** 修改 AudioApi.transcribeAudio 方法

```javascript
async transcribeAudio(filePath, config = {}) {
  const request = this.backend.client.post('/api/audio/transcribe', {
    file_path: filePath,
    model: config.model,
  })
  return await request.json()
}
```

**Step 2:** 更新 MinerUApi 方法（如需要）

**Step 3:** 提交

```bash
git add app/src/utils/backend.js
git commit -m "refactor: simplify backend API parameters"
```

---

### Task 10: 更新 Settings.vue - 集成新组件

**Files:**
- Modify: `app/src/components/Settings.vue`

**Step 1:** 读取现有 Settings.vue 结构

**Step 2:** 添加音频解析设置 tab

**Step 3:** 更新 PDF 解析设置引用

**Step 4:** 提交

```bash
git add app/src/components/Settings.vue
git commit -m "feat: integrate new parse settings components"
```

---

## 第三阶段：验证与测试

### Task 11: 运行前端构建检查

**Step 1:** 运行 lint 检查

```bash
cd app
npm run lint
```

**Step 2:** 运行 typecheck（如果有）

**Step 3:** 运行 build 检查

```bash
npm run build
```

---

### Task 12: 更新文档（可选）

**Files:**
- Update: `docs/features/` 相关文档（如需要）

---

## 总结

### 文件变更总览

**后端：**
- `backend/.env.example` - 添加硅基流动配置
- `backend/src/models/audio_schemas.py` - 简化请求 schema
- `backend/src/api/audio.py` - 简化 API
- `backend/src/processors/audio_processor.py` - 更新处理器
- `backend/src/api/mineru.py` - 增强配置选项
- `backend/src/mineru/client.py` - 支持配置选项

**前端：**
- `app/src/stores/parse.js` - 新增
- `app/src/stores/agent.js` - 清理
- `app/src/components/settings/AudioParseSettings.vue` - 新增
- `app/src/components/settings/PdfParseSettings.vue` - 修改
- `app/src/processors/parse/AudioTranscriber.js` - 更新
- `app/src/utils/backend.js` - 更新
- `app/src/components/Settings.vue` - 集成

---

**Plan complete and saved to `docs/plans/2026-03-03-parse-config-unification.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
