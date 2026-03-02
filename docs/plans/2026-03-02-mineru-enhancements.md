# MinerU 增强实施计划

&gt; **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完善 MinerU API Payload，增强错误处理，添加连接测试功能

**Architecture:** 
1. 更新 Electron 主进程以支持完整的 API 配置和更好的错误处理
2. 更新前端传递完整配置对象而非仅 API Key
3. 添加 UI 测试连接功能和高级选项
4. 增强错误提示，提供友好的中文信息和修复建议

**Tech Stack:** Electron + Node.js + Vue 3 + Element Plus

---

## 前提条件检查

### 检查当前文件
确认以下文件存在且可访问：
- `app/electron/main.js`
- `app/electron/preload.js`
- `app/src/processors/MinerUProcessor.js`
- `app/src/processors/parse/TextExtractor.js`
- `app/src/components/settings/PdfParseSettings.vue`
- `app/src/stores/agent.js`

---

## Task 1: 更新 Store 配置结构

**Files:**
- Modify: `app/src/stores/agent.js:42-58`

**Step 1: 读取当前 store 文件**

确认当前 llmConfig 结构。

**Step 2: 更新 mineru 配置对象**

将 mineru 配置从：
```javascript
mineru: {
  apiKey: '',
  baseUrl: 'https://mineru.net',
}
```

更新为：
```javascript
mineru: {
  apiKey: '',
  baseUrl: 'https://mineru.net',
  enableFormula: true,
  enableTable: true,
  enableOcr: true,
  language: 'auto'
}
```

**Step 3: 验证变更**

检查文件语法正确。

---

## Task 2: 更新 Electron Preload API

**Files:**
- Modify: `app/electron/preload.js:18`

**Step 1: 修改 extractPdf 签名**

将：
```javascript
extractPdf: (filePath, apiKey) =&gt; ipcRenderer.invoke('mineru:extract-pdf', filePath, apiKey)
```

改为：
```javascript
extractPdf: (filePath, config) =&gt; ipcRenderer.invoke('mineru:extract-pdf', filePath, config)
```

---

## Task 3: 更新 MinerUProcessor

**Files:**
- Modify: `app/src/processors/MinerUProcessor.js:9-15`

**Step 1: 更新 extractText 方法**

将：
```javascript
async extractText(file) {
  if (!this.config.apiKey) {
    throw new Error('MinerU API key not configured')
  }
  const result = await window.electronAPI.mineru.extractPdf(file.path, this.config.apiKey)
  return result
}
```

改为：
```javascript
async extractText(file) {
  if (!this.config.apiKey) {
    throw new Error('MinerU API key not configured')
  }
  const result = await window.electronAPI.mineru.extractPdf(file.path, this.config)
  return result
}
```

---

## Task 4: 增强 Electron 主进程实现

**Files:**
- Modify: `app/electron/main.js:313-431`

**Step 1: 修改处理器签名**

将：
```javascript
ipcMain.handle('mineru:extract-pdf', async (event, filePath, apiKey) =&gt; {
```

改为：
```javascript
ipcMain.handle('mineru:extract-pdf', async (event, filePath, config) =&gt; {
  const {
    apiKey,
    baseUrl = 'https://mineru.net',
    enableFormula = true,
    enableTable = true,
    enableOcr = true,
    language = 'auto'
  } = config || {}
```

**Step 2: 解析自定义 Base URL**

在获取上传 URL 之前添加：
```javascript
  const parsedBaseUrl = new URL(baseUrl)
  const hostname = parsedBaseUrl.hostname
  const port = parsedBaseUrl.port || (parsedBaseUrl.protocol === 'https:' ? 443 : 80)
```

**Step 3: 更新 makeRequest 调用以使用动态 hostname**

将所有硬编码的 `hostname: 'mineru.net'` 和 `port: 443` 替换为动态变量。

**Step 4: 更新 API Payload**

将：
```javascript
  }, {
    files: [{ name: fileName }],
    model_version: 'vlm'
  })
```

改为：
```javascript
  }, {
    language,
    enable_formula: enableFormula,
    enable_table: enableTable,
    files: [{
      name: fileName,
      is_ocr: enableOcr
    }]
  })
```

**Step 5: 增强错误处理**

在各个错误点添加分类处理：
- API Key 错误 (A0202, A0211)
- 网络错误
- 超时错误
- 文件格式错误

---

## Task 5: 增强 TextExtractor 错误处理

**Files:**
- Modify: `app/src/processors/parse/TextExtractor.js:116-129`

**Step 1: 扩展错误映射**

将当前的错误处理更新为：
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
      let suggestion = ''

      if (errorMessage.includes('A0202') || errorMessage.includes('A0211') || 
          errorMessage.includes('API Key') || errorMessage.includes('API key')) {
        errorMessage = 'MinerU API Key 无效或已过期'
        suggestion = '请在设置中检查您的 API Key 是否正确'
      } else if (errorMessage.includes('ECONNRESET') || errorMessage.includes('network') || 
                 errorMessage.includes('ENOTFOUND') || errorMessage.includes('连接')) {
        errorMessage = 'MinerU 网络连接失败'
        suggestion = '请检查网络连接或稍后重试'
      } else if (errorMessage.includes('Timeout') || errorMessage.includes('超时')) {
        errorMessage = 'MinerU 解析超时'
        suggestion = '请稍后重试，或尝试拆分较大的 PDF 文件'
      } else if (errorMessage.includes('format') || errorMessage.includes('损坏') || 
                 errorMessage.includes('corrupted')) {
        errorMessage = 'PDF 文件格式不支持或已损坏'
        suggestion = '请尝试使用其他 PDF 文件，或修复当前文件'
      }

      const fullMessage = suggestion ? `${errorMessage}。${suggestion}` : errorMessage
      throw new Error(fullMessage)
    }
  }
```

---

## Task 6: 更新 PdfParseSettings - 添加测试连接和高级选项

**Files:**
- Modify: `app/src/components/settings/PdfParseSettings.vue`

**Step 1: 更新模板 - 添加测试按钮和高级选项**

在 Base URL 表单项后添加：
```vue
      &lt;el-form-item&gt;
        &lt;el-button :loading="isTesting" @click="handleTestConnection" type="primary"&gt;
          测试连接
        &lt;/el-button&gt;
      &lt;/el-form-item&gt;

      &lt;el-divider content-position="left"&gt;高级选项&lt;/el-divider&gt;

      &lt;el-form-item label="启用公式识别"&gt;
        &lt;el-switch v-model="mineruConfig.enableFormula" /&gt;
      &lt;/el-form-item&gt;

      &lt;el-form-item label="启用表格识别"&gt;
        &lt;el-switch v-model="mineruConfig.enableTable" /&gt;
      &lt;/el-form-item&gt;

      &lt;el-form-item label="启用 OCR"&gt;
        &lt;el-switch v-model="mineruConfig.enableOcr" /&gt;
      &lt;/el-form-item&gt;

      &lt;el-form-item label="语言"&gt;
        &lt;el-select v-model="mineruConfig.language" style="width: 200px"&gt;
          &lt;el-option label="自动检测" value="auto" /&gt;
          &lt;el-option label="中文" value="zh" /&gt;
          &lt;el-option label="英文" value="en" /&gt;
        &lt;/el-select&gt;
      &lt;/el-form-item&gt;
```

**Step 2: 更新 script - 添加测试逻辑和新配置项**

更新导入：
```javascript
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { ElMessage } from 'element-plus'
```

更新状态变量：
```javascript
const isUpdating = ref(false)
const isTesting = ref(false)

const parseStrategy = ref('mineru')
const mineruConfig = ref({
  apiKey: '',
  baseUrl: '',
  enableFormula: true,
  enableTable: true,
  enableOcr: true,
  language: 'auto'
})
```

添加测试连接函数：
```javascript
async function handleTestConnection() {
  if (!mineruConfig.value.apiKey) {
    ElMessage.warning('请先输入 MinerU API Key')
    return
  }

  isTesting.value = true
  try {
    ElMessage.info('正在测试 MinerU 连接...')
    
    const baseUrl = mineruConfig.value.baseUrl || 'https://mineru.net'
    const response = await fetch(`${baseUrl}/api/v4/file-urls/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${mineruConfig.value.apiKey}`,
      },
      body: JSON.stringify({
        language: 'auto',
        enable_formula: true,
        enable_table: true,
        files: [{ name: 'test.pdf', is_ocr: true }],
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
```

---

## Task 7: 添加新的 IPC 处理函数 - 测试连接

**Files:**
- Modify: `app/electron/main.js` (在 mineru:extract-pdf 后添加)

**Step 1: 添加测试连接处理函数**

```javascript
ipcMain.handle('mineru:test-connection', async (event, config) =&gt; {
  const { apiKey, baseUrl = 'https://mineru.net' } = config || {}
  
  if (!apiKey) {
    return { success: false, message: 'API Key 未配置' }
  }

  try {
    const parsedBaseUrl = new URL(baseUrl)
    const hostname = parsedBaseUrl.hostname
    const port = parsedBaseUrl.port || (parsedBaseUrl.protocol === 'https:' ? 443 : 80)

    const result = await makeRequest({
      hostname,
      port,
      path: '/api/v4/file-urls/batch',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      }
    }, {
      language: 'auto',
      enable_formula: true,
      enable_table: true,
      files: [{ name: 'test.pdf', is_ocr: true }]
    })

    if (result.data.code === 0 || result.data.code === -60002) {
      return { success: true, message: '连接成功' }
    } else {
      return { success: false, message: result.data.msg || `错误码: ${result.data.code}` }
    }
  } catch (error) {
    return { success: false, message: error.message }
  }
})
```

**Step 2: 更新 preload.js 暴露新 API**

在 `app/electron/preload.js` 的 mineru 对象中添加：
```javascript
testConnection: (config) =&gt; ipcRenderer.invoke('mineru:test-connection', config)
```

---

## Task 8: 运行验证

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

- [ ] Store 配置包含 `enableFormula`、`enableTable`、`enableOcr`、`language`
- [ ] Preload API 传递完整 config 对象
- [ ] MinerUProcessor 传递完整配置
- [ ] Electron 主进程支持自定义 Base URL 和完整 API Payload
- [ ] 错误处理增强且提示友好
- [ ] PdfParseSettings 有测试连接按钮
- [ ] PdfParseSettings 有高级选项开关
- [ ] `npm run lint` 通过
- [ ] `npm run format` 通过

---

Plan complete and saved to `docs/plans/2026-03-02-mineru-enhancements.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
