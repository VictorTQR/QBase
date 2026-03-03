# 解析功能修复 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复QBase解析相关功能的所有问题，包括文档解析、音频解析、向量解析的bug修复和功能完善。

**Architecture:** 分三个阶段修复：快速修复（立即可见效果）、高优先级修复（核心功能）、中优先级优化（体验提升）。每个任务独立可提交。

**Tech Stack:** Vue 3 + Pinia + Element Plus + FastAPI

---

## 阶段一：快速修复（立即可见效果）

### Task 1: 修复 indexedFilesCount 显示错误

**Files:**
- Modify: `app/src/components/parse/ParseStatsView.vue:155`

**Step 1: 定位问题代码**

查看 `ParseStatsView.vue` 第155行：
```javascript
const indexedFilesCount = computed(() => vectorStore.indexedFiles.size)
```

**Step 2: 修复计算错误**

修改为：
```javascript
const indexedFilesCount = computed(() => Object.keys(vectorStore.indexedFiles).length)
```

**Step 3: 验证修复**

打开解析管理页面的统计面板，确认"已索引文档"显示正确数字。

**Step 4: Commit**

```bash
cd app
git add src/components/parse/ParseStatsView.vue
git commit -m "fix: 修复已索引文档计数显示错误"
```

---

### Task 2: 为 parseBackend.js 添加错误处理

**Files:**
- Modify: `app/src/api/parseBackend.js`

**Step 1: 重写 parseBackend.js 所有方法**

参考 `vectorBackend.js` 的错误处理模式，重写所有API方法：

```javascript
import { backendService as backend } from '@/utils/backend'

export class ParseBackendApi {
  static async checkDuplicate(params) {
    try {
      const request = backend.client.post('/api/mineru/check-duplicate', params)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] checkDuplicate 失败:', error)
      throw new Error('去重检查失败')
    }
  }

  static async parseFile(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const request = backend.client.post('/api/mineru/parse', formData)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] parseFile 失败:', error)
      throw new Error('文件解析失败')
    }
  }

  static async parseLocalFile(filePath) {
    try {
      const request = backend.client.post('/api/mineru/parse-local', {
        file_path: filePath,
      })
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] parseLocalFile 失败:', error)
      throw new Error('本地文件解析失败')
    }
  }

  static async getTask(taskId) {
    try {
      const request = backend.client.get(`/api/mineru/tasks/${taskId}`)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] getTask 失败:', error)
      throw new Error('获取任务状态失败')
    }
  }

  static async listTasks(limit = 100, offset = 0) {
    try {
      const request = backend.client.get(`/api/mineru/tasks?limit=${limit}&offset=${offset}`)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] listTasks 失败:', error)
      throw new Error('获取任务列表失败')
    }
  }

  static async getStats() {
    try {
      const request = backend.client.get('/api/mineru/stats')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] getStats 失败:', error)
      throw new Error('获取统计数据失败')
    }
  }

  static async getTaskResult(taskId) {
    try {
      const request = backend.client.get(`/api/mineru/tasks/${taskId}/result`)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] getTaskResult 失败:', error)
      throw new Error('获取解析结果失败')
    }
  }

  static async downloadResult(taskId) {
    try {
      return backend.client.get(`/api/mineru/tasks/${taskId}/download`)
    } catch (error) {
      console.error('[ParseBackendApi] downloadResult 失败:', error)
      throw new Error('下载结果失败')
    }
  }

  static async clearCompleted() {
    try {
      const request = backend.client.delete('/api/mineru/tasks/clear-completed')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] clearCompleted 失败:', error)
      throw new Error('清除已完成任务失败')
    }
  }

  static async clearAll() {
    try {
      const request = backend.client.delete('/api/mineru/tasks/clear-all')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] clearAll 失败:', error)
      throw new Error('清空任务失败')
    }
  }

  static async batchParsePending() {
    try {
      const request = backend.client.post('/api/mineru/tasks/batch-parse-pending')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] batchParsePending 失败:', error)
      throw new Error('批量解析失败')
    }
  }

  static async retryFailed() {
    try {
      const request = backend.client.post('/api/mineru/tasks/retry-failed')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] retryFailed 失败:', error)
      throw new Error('重试失败任务失败')
    }
  }
}
```

**Step 2: 验证修复**

确保所有方法都有 try-catch 包裹，并有适当的错误日志。

**Step 3: Commit**

```bash
cd app
git add src/api/parseBackend.js
git commit -m "fix: 为parseBackend添加错误处理"
```

---

### Task 3: 在 ParseQueueView 添加批量操作按钮

**Files:**
- Modify: `app/src/components/parse/ParseQueueView.vue:5-23`

**Step 1: 添加状态变量**

在 `<script setup>` 中添加：
```javascript
const isBatchParsing = ref(false)
const isRetrying = ref(false)
```

**Step 2: 添加批量操作函数**

```javascript
const handleBatchParse = async () => {
  if (pendingTasks.value.length === 0) {
    ElMessage.warning('没有待解析的文件')
    return
  }

  try {
    isBatchParsing.value = true
    const response = await parseStore.batchParsePending()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '批量解析失败')
  } finally {
    isBatchParsing.value = false
  }
}

const handleRetryFailed = async () => {
  if (failedTasks.value.length === 0) {
    ElMessage.warning('没有失败的文件')
    return
  }

  try {
    isRetrying.value = true
    const response = await parseStore.retryFailedTasks()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '重试失败')
  } finally {
    isRetrying.value = false
  }
}
```

**Step 3: 修改模板中的按钮区域**

在 `<template>` 中修改 header-actions：

```vue
<div class="header-actions">
  <el-button
    size="small"
    :disabled="pendingTasks.length === 0 || isBatchParsing"
    :loading="isBatchParsing"
    @click="handleBatchParse"
  >
    批量解析
  </el-button>
  <el-button
    size="small"
    type="warning"
    :disabled="failedTasks.length === 0 || isRetrying"
    :loading="isRetrying"
    @click="handleRetryFailed"
  >
    重试失败
  </el-button>
  <el-divider direction="vertical" />
  <el-button
    size="small"
    :disabled="doneTasks.length === 0 || isClearingCompleted"
    :loading="isClearingCompleted"
    @click="handleClearCompleted"
  >
    清除已完成
  </el-button>
  <el-button
    size="small"
    type="danger"
    :disabled="parseStore.tasks.length === 0 || isClearingAll"
    :loading="isClearingAll"
    @click="handleClearAll"
  >
    清空队列
  </el-button>
</div>
```

**Step 4: Commit**

```bash
cd app
git add src/components/parse/ParseQueueView.vue
git commit -m "feat: 在队列管理页面添加批量解析和重试按钮"
```

---

## 阶段二：高优先级修复（核心功能）

### Task 4: 创建 audioBackend.js API文件

**Files:**
- Create: `app/src/api/audioBackend.js`

**Step 1: 创建新文件**

```javascript
import { backendService as backend } from '@/utils/backend'

export class AudioBackendApi {
  static async transcribeUpload(file, model) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (model) {
        formData.append('model', model)
      }
      const request = backend.client.post('/api/audio/transcribe-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] transcribeUpload 失败:', error)
      throw new Error('音频上传转录失败')
    }
  }

  static async transcribeLocal(filePath, model) {
    try {
      const request = backend.client.post('/api/audio/transcribe-local', {
        file_path: filePath,
        model,
      })
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] transcribeLocal 失败:', error)
      throw new Error('本地音频转录失败')
    }
  }

  static async transcribe(filePath, model) {
    try {
      const request = backend.client.post('/api/audio/transcribe', {
        file_path: filePath,
        model,
      })
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] transcribe 失败:', error)
      throw new Error('音频转录失败')
    }
  }

  static async getTask(taskId) {
    try {
      const request = backend.client.get(`/api/audio/tasks/${taskId}`)
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] getTask 失败:', error)
      throw new Error('获取音频任务状态失败')
    }
  }

  static async getTaskResult(taskId) {
    try {
      const request = backend.client.get(`/api/audio/tasks/${taskId}/result`)
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] getTaskResult 失败:', error)
      throw new Error('获取音频转录结果失败')
    }
  }

  static async listTasks() {
    try {
      const request = backend.client.get('/api/audio/tasks')
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] listTasks 失败:', error)
      throw new Error('获取音频任务列表失败')
    }
  }

  static async deleteTask(taskId) {
    try {
      const request = backend.client.delete(`/api/audio/tasks/${taskId}`)
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] deleteTask 失败:', error)
      throw new Error('删除音频任务失败')
    }
  }
}
```

**Step 2: Commit**

```bash
cd app
git add src/api/audioBackend.js
git commit -m "feat: 创建音频解析API客户端"
```

---

### Task 5: 创建 audio.js Store

**Files:**
- Create: `app/src/stores/audio.js`

**Step 1: 创建新文件**

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { AudioBackendApi } from '@/api/audioBackend'

export const useAudioStore = defineStore('audio', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const tasksByStatus = computed(() => {
    const groups = {
      pending: [],
      processing: [],
      completed: [],
      failed: [],
    }
    tasks.value.forEach((task) => {
      if (groups[task.status]) {
        groups[task.status].push(task)
      }
    })
    return groups
  })

  const pendingTasks = computed(() => tasksByStatus.value.pending)
  const processingTasks = computed(() => tasksByStatus.value.processing)
  const completedTasks = computed(() => tasksByStatus.value.completed)
  const failedTasks = computed(() => tasksByStatus.value.failed)

  async function fetchTasks() {
    isLoading.value = true
    error.value = null
    try {
      const response = await AudioBackendApi.listTasks()
      tasks.value = response.tasks || []
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTask(taskId) {
    try {
      const task = await AudioBackendApi.getTask(taskId)
      const index = tasks.value.findIndex((t) => t.task_id === taskId)
      if (index !== -1) {
        tasks.value[index] = task
      }
      currentTask.value = task
      return task
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function transcribeLocalFile(filePath, model) {
    isLoading.value = true
    error.value = null
    try {
      const result = await AudioBackendApi.transcribeLocal(filePath, model)
      await fetchTasks()
      return result
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function transcribeUploadFile(file, model) {
    isLoading.value = true
    error.value = null
    try {
      const result = await AudioBackendApi.transcribeUpload(file, model)
      await fetchTasks()
      return result
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getTaskResult(taskId) {
    try {
      return await AudioBackendApi.getTaskResult(taskId)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function deleteTask(taskId) {
    try {
      await AudioBackendApi.deleteTask(taskId)
      await fetchTasks()
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function pollTaskUntilDone(taskId, interval = 3000, maxAttempts = 600) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const task = await fetchTask(taskId)
      if (task.status === 'completed') {
        return { success: true, task }
      } else if (task.status === 'failed') {
        return { success: false, error: task.error || '转录失败', task }
      }
      await new Promise((resolve) => setTimeout(resolve, interval))
    }
    return { success: false, error: '超时' }
  }

  function clearError() {
    error.value = null
  }

  return {
    tasks,
    currentTask,
    isLoading,
    error,
    tasksByStatus,
    pendingTasks,
    processingTasks,
    completedTasks,
    failedTasks,
    fetchTasks,
    fetchTask,
    transcribeLocalFile,
    transcribeUploadFile,
    getTaskResult,
    deleteTask,
    pollTaskUntilDone,
    clearError,
  }
})
```

**Step 2: Commit**

```bash
cd app
git add src/stores/audio.js
git commit -m "feat: 创建音频解析状态管理Store"
```

---

### Task 6: 在 ParseSidebar 添加音频解析导航

**Files:**
- Modify: `app/src/components/Layout/ParseSidebar.vue:28-32`

**Step 1: 导入新图标**

```javascript
import { Document, List, TrendCharts, Microphone } from '@element-plus/icons-vue'
```

**Step 2: 添加音频解析导航项**

```javascript
const navItems = [
  { key: 'queue', label: '队列管理', icon: Document },
  { key: 'documents', label: '已解析文档', icon: List },
  { key: 'audio', label: '音频解析', icon: Microphone },
  { key: 'stats', label: '解析统计', icon: TrendCharts },
]
```

**Step 3: Commit**

```bash
cd app
git add src/components/Layout/ParseSidebar.vue
git commit -m "feat: 在解析侧边栏添加音频解析导航"
```

---

### Task 7: 在 ParseManagement 添加音频解析视图路由

**Files:**
- Modify: `app/src/views/ParseManagement.vue`

**Step 1: 添加音频视图占位符**

由于还没有音频解析组件，先添加一个简单的占位组件，或者创建一个基础的音频解析视图。

首先，创建一个基础的音频解析视图：

**Files:**
- Create: `app/src/components/parse/AudioParseView.vue`

```vue
<template>
  <div class="audio-parse-view">
    <div class="view-header">
      <h2>音频解析</h2>
    </div>
    <el-empty description="音频解析功能开发中..." />
  </div>
</template>

<script setup>
</script>

<style scoped>
.audio-parse-view {
  height: 100%;
}
.view-header {
  margin-bottom: 20px;
}
.view-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}
</style>
```

**Step 2: 在 ParseManagement.vue 中导入和注册**

```javascript
import AudioParseView from '@/components/parse/AudioParseView.vue'

const componentMap = {
  queue: ParseQueueView,
  documents: ParseDocumentsView,
  audio: AudioParseView,
  stats: ParseStatsView,
}
```

**Step 3: Commit**

```bash
cd app
git add src/components/parse/AudioParseView.vue
git add src/views/ParseManagement.vue
git commit -m "feat: 添加音频解析视图占位符"
```

---

## 阶段三：中优先级优化

### Task 8: 为 vectorBackend.js searchVectors 添加错误处理

**Files:**
- Modify: `app/src/api/vectorBackend.js:30-34`

**Step 1: 重写 searchVectors 方法**

```javascript
static async searchVectors(params) {
  console.log('[VectorBackendApi] searchVectors 调用，参数:', params)
  try {
    const request = backend.client.post('/api/vector/search', params)
    return await request.json()
  } catch (error) {
    console.error('[VectorBackendApi] searchVectors 失败:', error)
    if (error.response) {
      try {
        const errorData = await error.response.json()
        throw new Error(errorData.detail || errorData.message || '向量搜索失败')
      } catch (e) {
        throw new Error(`向量搜索失败 (${error.response.status})`)
      }
    }
    throw error
  }
}
```

**Step 2: Commit**

```bash
cd app
git add src/api/vectorBackend.js
git commit -m "fix: 为向量搜索添加错误处理"
```

---

### Task 9: 清理 console.log 调试语句

**Files:**
- Modify: `app/src/api/vectorBackend.js`
- Modify: `app/src/stores/vector.js`

**Step 1: 清理 vectorBackend.js**

保留错误日志，移除普通调试日志，或封装为调试模式。

```javascript
// 将 console.log 改为可选的调试日志
const DEBUG = import.meta.env.DEV

static async indexDocument(params) {
  if (DEBUG) console.log('[VectorBackendApi] indexDocument 调用，参数:', params)
  try {
    const request = backend.client.post('/api/vector/index', params)
    const response = await request
    if (DEBUG) console.log('[VectorBackendApi] 响应状态:', response.status)
    const result = await response.json()
    if (DEBUG) console.log('[VectorBackendApi] 响应数据:', result)
    return result
  } catch (error) {
    console.error('[VectorBackendApi] 请求失败:', error)
    // ... 其余错误处理保持不变
  }
}
```

对 `searchVectors`、`deleteDocumentChunks`、`getVectorStats`、`clearAllVectors` 做同样处理。

**Step 2: 清理 vector.js store**

```javascript
// 同样添加 DEBUG 条件
const DEBUG = import.meta.env.DEV

async function indexDocument(filePath, fileName, content, workspaceId) {
  // ...
  if (DEBUG) console.log('[VectorStore] 准备索引文档，请求参数:', requestParams)
  if (DEBUG) console.log('[VectorStore] content 长度:', content?.length || 0)
  if (DEBUG) console.log('[VectorStore] workspace_id (处理后):', requestParams.workspace_id)
  // ...
}
```

**Step 3: Commit**

```bash
cd app
git add src/api/vectorBackend.js src/stores/vector.js
git commit -m "refactor: 用DEBUG条件包裹调试日志"
```

---

## 执行总结

### 阶段一完成标准
- [ ] Task 1: indexedFilesCount 显示正确
- [ ] Task 2: parseBackend.js 所有方法有错误处理
- [ ] Task 3: ParseQueueView 有批量解析和重试按钮

### 阶段二完成标准
- [ ] Task 4: audioBackend.js 创建完成
- [ ] Task 5: audio.js store 创建完成
- [ ] Task 6: ParseSidebar 有音频解析导航
- [ ] Task 7: ParseManagement 可切换到音频解析视图

### 阶段三完成标准
- [ ] Task 8: searchVectors 有错误处理
- [ [ Task 9: 调试日志已清理

---

**Plan complete and saved to `docs/plans/2026-03-03-parse-features-fix.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
