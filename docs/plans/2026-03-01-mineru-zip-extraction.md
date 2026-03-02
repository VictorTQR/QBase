# MinerU ZIP 解压与文本提取修复计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 MinerU PDF 解析功能，正确处理返回的 ZIP 文件并提取 Markdown 文本内容。

**Architecture:** 
1. 在 Electron 主进程中添加 JSZip 库来解压 ZIP 文件
2. 从解压后的文件中找到并读取 Markdown 内容
3. 返回纯文本给渲染进程
4. 增强错误处理，提供友好的错误提示
5. 添加连接测试功能

**Tech Stack:** Node.js + JSZip + Electron IPC

---

## 前提条件检查

### 检查 package.json 依赖

首先检查 `app/package.json` 是否已有 JSZip 依赖，如没有需要安装。

---

## 任务清单

### Task 1: 检查并安装 JSZip 依赖

**Files:**
- Check: `app/package.json`
- Install: JSZip (if needed)

**Step 1: 检查当前依赖**

读取 `app/package.json` 查看 dependencies

**Step 2: 安装 JSZip（如需要）**

如果没有 JSZip，运行：
```bash
cd app
npm install jszip
```

---

### Task 2: 修改 Electron 主进程 - 解压 ZIP 并提取文本

**Files:**
- Modify: `app/electron/main.js:273-341`

**Step 1: 引入 JSZip**

在文件顶部添加：
```javascript
const JSZip = require('jszip')
```

**Step 2: 重写 mineru:extract-pdf 处理函数**

替换 `mineru:extract-pdf` IPC 处理函数（约第 273-341 行）：

```javascript
ipcMain.handle('mineru:extract-pdf', async (event, filePath, apiKey) => {
  const fileName = path.basename(filePath)
  const fileData = fs.readFileSync(filePath)

  const uploadResult = await makeRequest({
    hostname: 'mineru.net',
    port: 443,
    path: '/api/v4/file-urls/batch',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    }
  }, {
    files: [{ name: fileName }],
    model_version: 'vlm'
  })

  if (uploadResult.data.code !== 0) {
    throw new Error(uploadResult.data.msg || 'Failed to get upload URL')
  }

  const batchId = uploadResult.data.data.batch_id
  const uploadUrl = uploadResult.data.data.file_urls[0]

  await uploadFile(uploadUrl, fileData)

  await new Promise(resolve => setTimeout(resolve, 5000))

  let maxAttempts = 60
  let attempts = 0
  let taskResult = null

  while (attempts < maxAttempts) {
    const pollResult = await makeRequest({
      hostname: 'mineru.net',
      port: 443,
      path: `/api/v4/extract-results/batch/${batchId}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    })

    if (pollResult.data.code === 0 && pollResult.data.data.extract_result) {
      const fileResult = pollResult.data.data.extract_result[0]
      if (fileResult.state === 'done') {
        taskResult = fileResult
        break
      } else if (fileResult.state === 'failed') {
        throw new Error(fileResult.err_msg || 'Parsing failed')
      }
    }

    attempts++
    await new Promise(resolve => setTimeout(resolve, 3000))
  }

  if (!taskResult) {
    throw new Error('Timeout waiting for parsing result')
  }

  const zipBuffer = await downloadFile(taskResult.full_zip_url)

  const zip = await JSZip.loadAsync(zipBuffer)
  let markdownContent = ''

  for (const [filename, file] of Object.entries(zip.files)) {
    if (filename.endsWith('.md') && !file.dir) {
      markdownContent = await file.async('string')
      break
    }
  }

  if (!markdownContent) {
    throw new Error('No markdown file found in ZIP result')
  }

  return markdownContent
})
```

---

### Task 3: 修改 MinerUProcessor - 正确处理返回结果

**Files:**
- Modify: `app/src/processors/MinerUProcessor.js`

**Step 1: 更新 extractText 方法**

由于现在 main.js 直接返回 markdownContent 字符串，MinerUProcessor 可以保持简单：

```javascript
import { DocumentProcessor } from './DocumentProcessor.js'

export class MinerUProcessor extends DocumentProcessor {
  constructor(config) {
    super()
    this.config = config
  }

  async extractText(file) {
    if (!this.config.apiKey) {
      throw new Error('MinerU API key not configured')
    }
    const result = await window.electronAPI.mineru.extractPdf(file.path, this.config.apiKey)
    return result
  }

  async extractStructured(file) {
    return await this.extractText(file)
  }
}
```

（这个文件实际上已经是正确的了，保持不变即可）

---

### Task 4: 修改 PdfParseSettings - 添加 MinerU 连接测试

**Files:**
- Modify: `app/src/components/settings/PdfParseSettings.vue`

**Step 1: 添加测试按钮和状态**

在模板中 MinerU 配置部分添加测试按钮：

```vue
<template>
  <div class="pdf-parse-settings">
    <el-form label-width="140px">
      <el-form-item label="解析策略">
        <el-radio-group v-model="parseStrategy">
          <el-radio value="local">仅本地解析</el-radio>
          <el-radio value="mineru">仅 MinerU 解析</el-radio>
          <el-radio value="auto">优先本地，失败降级</el-radio>
        </el-radio-group>
        <div class="form-item-desc">
          <el-text type="info" size="small">未来将支持更多解析方式</el-text>
        </div>
      </el-form-item>

      <el-divider content-position="left">MinerU 配置</el-divider>

      <el-form-item label="API Key">
        <el-input
          v-model="mineruConfig.apiKey"
          type="password"
          show-password
          placeholder="请输入 MinerU API Key"
        />
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="mineruConfig.baseUrl" />
      </el-form-item>
      <el-form-item>
        <el-button :loading="isTesting" @click="handleTestConnection" type="primary">
          测试连接
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
```

**Step 2: 添加测试逻辑**

在 script 中添加测试连接功能：

```javascript
<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { ElMessage } from 'element-plus'

const agentStore = useAgentStore()
const isUpdating = ref(false)
const isTesting = ref(false)

const parseStrategy = ref('mineru')
const mineruConfig = ref({
  apiKey: '',
  baseUrl: '',
})

watch(
  () => agentStore.llmConfig,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    parseStrategy.value = config.parseStrategy || 'mineru'
    mineruConfig.value = { ...config.mineru }
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { immediate: true, deep: true },
)

watch(parseStrategy, (newStrategy) => {
  if (isUpdating.value) return
  isUpdating.value = true
  agentStore.setLlmConfig({
    ...agentStore.llmConfig,
    parseStrategy: newStrategy,
  })
  setTimeout(() => {
    isUpdating.value = false
  }, 0)
})

watch(
  mineruConfig,
  (newConfig) => {
    if (isUpdating.value) return
    isUpdating.value = true
    agentStore.setLlmConfig({
      ...agentStore.llmConfig,
      mineru: { ...newConfig },
    })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)

async function handleTestConnection() {
  if (!mineruConfig.value.apiKey) {
    ElMessage.warning('请先输入 MinerU API Key')
    return
  }

  isTesting.value = true
  try {
    ElMessage.info('正在测试 MinerU 连接...')
    
    const response = await fetch('https://mineru.net/api/v4/file-urls/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${mineruConfig.value.apiKey}`,
      },
      body: JSON.stringify({
        files: [{ name: 'test.pdf' }],
        model_version: 'vlm',
      }),
    })

    const result = await response.json()
    
    if (result.code === 0 || result.code === -60002) {
      ElMessage.success('MinerU 连接成功！')
    } else if (result.code === 'A0202' || result.code === 'A0211') {
      ElMessage.error('API Key 无效或已过期')
    } else {
      ElMessage.warning(`连接测试返回: ${result.msg || result.code}`)
    }
  } catch (err) {
    ElMessage.error(`连接测试失败: ${err.message}`)
  } finally {
    isTesting.value = false
  }
}
</script>
```

---

### Task 5: 增强 TextExtractor 错误提示

**Files:**
- Modify: `app/src/processors/parse/TextExtractor.js:104-120`

**Step 1: 改进 extractWithMinerU 的错误处理**

```javascript
  static async extractWithMinerU(filePath, mineruConfig) {
    try {
      const processor = new MinerUProcessor(mineruConfig)
      const result = await processor.extractText({ path: filePath })

      return {
        text: result,
        fileType: 'pdf',
        extractedBy: 'mineru',
        extractedAt: new Date(),
        wordCount: result.split(/\s+/).filter(Boolean).length,
      }
    } catch (error) {
      console.error('MinerU 提取失败:', error)
      
      let errorMessage = error.message
      if (errorMessage.includes('ECONNRESET') || errorMessage.includes('network')) {
        errorMessage = 'MinerU 网络连接失败，请检查网络连接或稍后重试'
      } else if (errorMessage.includes('API key')) {
        errorMessage = 'MinerU API Key 未配置或无效，请在设置中检查'
      } else if (errorMessage.includes('Timeout')) {
        errorMessage = 'MinerU 解析超时，请稍后重试'
      }
      
      throw new Error(errorMessage)
    }
  }
```

---

### Task 6: 验证与测试

**Files:**
- All modified files

**Step 1: 运行 lint**

```bash
cd app
npm run lint
```

**Step 2: 运行 format**

```bash
npm run format
```

---

## 最终验证清单

- [ ] JSZip 已正确安装
- [ ] Electron 主进程能正确解压 ZIP 并提取 Markdown
- [ ] MinerUProcessor 能正确接收文本结果
- [ ] PdfParseSettings 有测试连接按钮且功能正常
- [ ] 错误提示友好且清晰
- [ ] npm run lint 通过
- [ ] npm run format 通过

---

Plan complete and saved to `docs/plans/2026-03-01-mineru-zip-extraction.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
