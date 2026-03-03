# 前端解析管理页面 - 完整重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 完全重写前端解析管理相关组件，直接使用新的后端 SQLite API，移除所有旧的 LocalStorage/IndexedDB 逻辑。

**架构：** 完全重构方案 - 重写 parseStore 只使用新 API，重写所有解析管理组件，移除向后兼容层，简化代码结构。

**技术栈：** Vue 3 + Pinia + Element Plus + 后端 SQLite API

---

## 前期准备

### Task 0: 确认后端 API 完整性

**Files:**
- Read: `app/src/api/parseBackend.js`

**Step 1:** 检查 parseBackend.js 的所有 API 方法

**确认以下方法存在：**
- `checkDuplicate(params)` - 去重检查
- `parseLocalFile(filePath)` - 本地文件解析
- `getTask(taskId)` - 获取单个任务
- `listTasks(limit, offset)` - 任务列表
- `getStats()` - 统计数据
- `getTaskResult(taskId)` - 获取解析结果
- `parseFile(file)` - 上传文件解析
- `downloadResult(taskId)` - 下载结果

**Step 2:** 如缺少方法则补充

---

## Phase 1: 重写 Parse Store

### Task 1: 完全重写 parseStore - 新接口

**Files:**
- Modify: `app/src/stores/parse.js`

**Step 1:** 完全重写 parse.js，使用新 API 接口

```javascript
import { ref, computed, onMounted } from 'vue'
import { defineStore } from 'pinia'
import { ParseBackendApi } from '@/api/parseBackend'

export const useParseStore = defineStore('parse', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const stats = ref({
    total: 0,
    pending: 0,
    running: 0,
    done: 0,
    failed: 0
  })
  const isLoading = ref(false)
  const error = ref(null)

  const tasksByState = computed(() => {
    const groups = {
      pending: [],
      running: [],
      done: [],
      failed: []
    }
    tasks.value.forEach(task => {
      if (groups[task.state]) {
        groups[task.state].push(task)
      }
    })
    return groups
  })

  const pendingTasks = computed(() => tasksByState.value.pending)
  const runningTasks = computed(() => tasksByState.value.running)
  const doneTasks = computed(() => tasksByState.value.done)
  const failedTasks = computed(() => tasksByState.value.failed)

  async function fetchTasks(limit = 100, offset = 0) {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.listTasks(limit, offset)
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
      const task = await ParseBackendApi.getTask(taskId)
      const index = tasks.value.findIndex(t => t.id === taskId)
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

  async function fetchStats() {
    try {
      const statsData = await ParseBackendApi.getStats()
      if (statsData) {
        stats.value = statsData
      }
      return stats.value
    } catch (err) {
      console.error('获取统计失败:', err)
    }
  }

  async function checkDuplicate(params) {
    try {
      return await ParseBackendApi.checkDuplicate(params)
    } catch (err) {
      console.error('去重检查失败:', err)
      return { is_duplicate: false }
    }
  }

  async function parseLocalFile(filePath) {
    isLoading.value = true
    error.value = null
    try {
      const task = await ParseBackendApi.parseLocalFile(filePath)
      if (!task.is_duplicate) {
        await fetchTasks()
        await fetchStats()
      }
      return task
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getTaskResult(taskId) {
    try {
      return await ParseBackendApi.getTaskResult(taskId)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function pollTaskUntilDone(taskId, interval = 3000, maxAttempts = 600) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const task = await fetchTask(taskId)
      if (task.state === 'done') {
        return { success: true, task }
      } else if (task.state === 'failed') {
        return { success: false, error: task.error_msg, task }
      }
      await new Promise(resolve => setTimeout(resolve, interval))
    }
    return { success: false, error: '超时' }
  }

  function getStateType(state) {
    const map = {
      done: 'success',
      running: 'primary',
      pending: 'warning',
      failed: 'danger'
    }
    return map[state] || 'info'
  }

  function getStateLabel(state) {
    const map = {
      done: '已完成',
      running: '解析中',
      pending: '待解析',
      failed: '失败'
    }
    return map[state] || state
  }

  function clearError() {
    error.value = null
  }

  onMounted(() => {
    fetchTasks()
    fetchStats()
  })

  return {
    tasks,
    currentTask,
    stats,
    isLoading,
    error,
    tasksByState,
    pendingTasks,
    runningTasks,
    doneTasks,
    failedTasks,
    fetchTasks,
    fetchTask,
    fetchStats,
    checkDuplicate,
    parseLocalFile,
    getTaskResult,
    pollTaskUntilDone,
    getStateType,
    getStateLabel,
    clearError,
  }
})
```

**Step 2:** 提交

```bash
git add app/src/stores/parse.js
git commit -m "refactor: completely rewrite parse store to use new backend API"
```

---

## Phase 2: 重写解析管理页面

### Task 2: 完全重写 ParseManagement.vue

**Files:**
- Modify: `app/src/views/ParseManagement.vue`

**Step 1:** 完全重写 ParseManagement.vue

```vue
<template>
  <div class="parse-management-page">
    <header class="page-header">
      <el-button @click="handleBack" link>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="header-title">解析管理</div>
      <div class="header-actions">
        <el-button size="small" :loading="parseStore.isLoading" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </header>

    <div v-if="parseStore.error" class="error-banner">
      <el-alert type="error" :closable="true" @close="parseStore.clearError">
        {{ parseStore.error }}
      </el-alert>
    </div>

    <div class="page-content">
      <ParseSidebar v-model="activeTab" />
      <div class="content-panel">
        <component :is="currentComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import ParseSidebar from '@/components/Layout/ParseSidebar.vue'
import ParseQueueView from '@/components/parse/ParseQueueView.vue'
import ParseDocumentsView from '@/components/parse/ParseDocumentsView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'

const router = useRouter()
const parseStore = useParseStore()
const activeTab = ref('queue')

const componentMap = {
  queue: ParseQueueView,
  documents: ParseDocumentsView,
  stats: ParseStatsView,
}

const currentComponent = computed(() => componentMap[activeTab.value] || ParseQueueView)

function handleBack() {
  router.push('/')
}

async function handleRefresh() {
  await parseStore.fetchTasks()
  await parseStore.fetchStats()
}
</script>

<style scoped>
.parse-management-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.error-banner {
  padding: 8px 16px;
}

.page-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-panel {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--el-bg-color);
}
</style>
```

**Step 2:** 提交

```bash
git add app/src/views/ParseManagement.vue
git commit -m "refactor: completely rewrite ParseManagement.vue"
```

---

### Task 3: 完全重写 ParseStatsView.vue

**Files:**
- Modify: `app/src/components/parse/ParseStatsView.vue`

**Step 1:** 完全重写 ParseStatsView.vue

```vue
<template>
  <div class="parse-stats-view">
    <div class="view-header">
      <h2>解析统计</h2>
    </div>

    <div class="stats-cards">
      <div class="stat-card total">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总计文件</div>
        </div>
      </div>
      <div class="stat-card completed">
        <div class="stat-icon">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.done }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div class="stat-card pending">
        <div class="stat-icon">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待解析</div>
        </div>
      </div>
      <div class="stat-card failed">
        <div class="stat-icon">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
    </div>

    <div class="stats-details">
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>快速操作</span>
          </div>
        </template>
        <div class="quick-actions">
          <el-button type="primary" disabled>
            批量解析待处理文件 (开发中)
          </el-button>
          <el-button type="warning" :disabled="stats.failed === 0" disabled>
            重试失败文件 (开发中)
          </el-button>
        </div>
      </el-card>

      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>解析状态分布</span>
          </div>
        </template>
        <div class="status-distribution">
          <div v-if="stats.total === 0" class="empty-distribution">
            暂无数据
          </div>
          <div v-else class="distribution-bar">
            <div
              v-for="item in distributionData"
              :key="item.status"
              class="distribution-segment"
              :class="item.status"
              :style="{ width: item.percentage + '%' }"
              :title="`${item.label}: ${item.count} (${item.percentage.toFixed(1)}%)`"
            />
          </div>
          <div class="distribution-legend">
            <div v-for="item in distributionData" :key="item.status" class="legend-item">
              <span class="legend-dot" :class="item.status"></span>
              <span class="legend-label">{{ item.label }}: {{ item.count }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document, CircleCheck, Clock, CircleClose } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'

const parseStore = useParseStore()

const stats = computed(() => parseStore.stats)

const distributionData = computed(() => {
  const total = stats.value.total || 0
  const items = [
    { status: 'done', label: '已完成', count: stats.value.done },
    { status: 'pending', label: '待解析', count: stats.value.pending },
    { status: 'running', label: '解析中', count: stats.value.running },
    { status: 'failed', label: '失败', count: stats.value.failed },
  ]
  return items.map(item => ({
    ...item,
    percentage: total > 0 ? (item.count / total) * 100 : 0,
  }))
})
</script>

<style scoped>
.parse-stats-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-header {
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-card.total .stat-icon {
  background: rgba(144, 147, 153, 0.1);
  color: var(--el-text-color-secondary);
}

.stat-card.completed .stat-icon {
  background: rgba(103, 194, 58, 0.1);
  color: var(--el-color-success);
}

.stat-card.pending .stat-icon {
  background: rgba(230, 162, 60, 0.1);
  color: var(--el-color-warning);
}

.stat-card.failed .stat-icon {
  background: rgba(245, 108, 108, 0.1);
  color: var(--el-color-danger);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.stats-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-card {
  margin-bottom: 0;
}

.card-header {
  font-weight: 600;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-distribution {
  padding: 16px 0;
}

.empty-distribution {
  text-align: center;
  color: var(--el-text-color-placeholder);
  padding: 40px 0;
}

.distribution-bar {
  height: 32px;
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 16px;
}

.distribution-segment {
  transition: width 0.3s;
}

.distribution-segment.done {
  background: var(--el-color-success);
}

.distribution-segment.pending {
  background: var(--el-color-warning);
}

.distribution-segment.running {
  background: var(--el-color-primary);
}

.distribution-segment.failed {
  background: var(--el-color-danger);
}

.distribution-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.done {
  background: var(--el-color-success);
}

.legend-dot.pending {
  background: var(--el-color-warning);
}

.legend-dot.running {
  background: var(--el-color-primary);
}

.legend-dot.failed {
  background: var(--el-color-danger);
}

.legend-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
```

**Step 2:** 提交

```bash
git add app/src/components/parse/ParseStatsView.vue
git commit -m "refactor: completely rewrite ParseStatsView.vue"
```

---

### Task 4: 完全重写 ParseQueueView.vue

**Files:**
- Modify: `app/src/components/parse/ParseQueueView.vue`

**Step 1:** 完全重写 ParseQueueView.vue

```vue
<template>
  <div class="parse-queue-view">
    <div class="view-header">
      <h2>队列管理</h2>
      <div class="header-actions">
        <el-button size="small" disabled>清除已完成 (开发中)</el-button>
        <el-button size="small" type="danger" disabled>
          清空队列 (开发中)
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeQueueTab" class="queue-tabs">
      <el-tab-pane label="解析中" name="running">
        <div v-if="runningTasks.length === 0" class="empty-state">
          <el-empty description="暂无解析中的任务" />
        </div>
        <div v-else class="task-list">
          <div v-for="task in runningTasks" :key="task.id" class="task-item">
            <div class="task-info">
              <div class="task-name">{{ task.file_name }}</div>
              <div class="task-path">{{ task.file_path || '未知路径' }}</div>
            </div>
            <el-tag type="primary" size="small">解析中</el-tag>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="待解析" name="pending">
        <div v-if="pendingTasks.length === 0" class="empty-state">
          <el-empty description="暂无待解析的任务" />
        </div>
        <div v-else class="task-list">
          <div v-for="task in pendingTasks" :key="task.id" class="task-item">
            <div class="task-info">
              <div class="task-name">{{ task.file_name }}</div>
              <div class="task-path">{{ task.file_path || '未知路径' }}</div>
            </div>
            <el-tag type="warning" size="small">待解析</el-tag>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="失败" name="failed">
        <div v-if="failedTasks.length === 0" class="empty-state">
          <el-empty description="暂无失败的任务" />
        </div>
        <div v-else class="task-list">
          <div v-for="task in failedTasks" :key="task.id" class="task-item">
            <div class="task-info">
              <div class="task-name">{{ task.file_name }}</div>
              <div class="task-path">{{ task.file_path || '未知路径' }}</div>
              <div v-if="task.error_msg" class="task-error">{{ task.error_msg }}</div>
            </div>
            <el-tag type="danger" size="small">失败</el-tag>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useParseStore } from '@/stores/parse'

const parseStore = useParseStore()
const activeQueueTab = ref('running')

const pendingTasks = computed(() => parseStore.pendingTasks)
const runningTasks = computed(() => parseStore.runningTasks)
const failedTasks = computed(() => parseStore.failedTasks)
</script>

<style scoped>
.parse-queue-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.queue-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.queue-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.queue-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

.empty-state {
  padding: 40px 0;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.task-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-error {
  font-size: 12px;
  color: var(--el-color-danger);
  margin-top: 4px;
}
</style>
```

**Step 2:** 提交

```bash
git add app/src/components/parse/ParseQueueView.vue
git commit -m "refactor: completely rewrite ParseQueueView.vue"
```

---

### Task 5: 完全重写 ParseDocumentsView.vue

**Files:**
- Modify: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1:** 完全重写 ParseDocumentsView.vue

```vue
<template>
  <div class="parse-documents-view">
    <div class="view-header">
      <h2>已解析文档</h2>
      <div class="header-tools">
        <el-input
          v-model="searchText"
          placeholder="搜索文档..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
        />
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="已完成" value="done" />
          <el-option label="解析中" value="running" />
          <el-option label="待解析" value="pending" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
    </div>

    <div v-if="filteredTasks.length === 0" class="empty-state">
      <el-empty description="暂无解析文档" />
    </div>
    <div v-else class="document-grid">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="document-card"
        @click="handleSelectTask(task)"
      >
        <div class="card-header">
          <el-icon class="status-icon" :class="task.state">
            <CircleCheck v-if="task.state === 'done'" />
            <Loading v-else-if="task.state === 'running'" class="spinning" />
            <Clock v-else-if="task.state === 'pending'" />
            <CircleClose v-else />
          </el-icon>
          <el-tag :type="parseStore.getStateType(task.state)" size="small">
            {{ parseStore.getStateLabel(task.state) }}
          </el-tag>
        </div>
        <div class="card-body">
          <div class="document-title">{{ task.file_name }}</div>
          <div class="document-path" :title="task.file_path">{{ task.file_path || '未知路径' }}</div>
        </div>
        <div class="card-footer">
          <span class="file-hash" v-if="task.file_hash">{{ task.file_hash.substring(0, 16) }}...</span>
          <span class="parser-type">{{ task.parser_type || 'mineru' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CircleCheck, Loading, Clock, CircleClose } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'

const parseStore = useParseStore()
const searchText = ref('')
const statusFilter = ref('')

const filteredTasks = computed(() => {
  let result = [...parseStore.tasks]

  if (statusFilter.value) {
    result = result.filter(task => task.state === statusFilter.value)
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(task =>
      (task.file_name && task.file_name.toLowerCase().includes(search)) ||
      (task.file_path && task.file_path.toLowerCase().includes(search))
    )
  }

  return result
})

function handleSelectTask(task) {
  console.log('选中任务:', task)
}
</script>

<style scoped>
.parse-documents-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.view-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.header-tools {
  display: flex;
  gap: 12px;
}

.empty-state {
  padding: 60px 0;
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  overflow-y: auto;
}

.document-card {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.2s;
}

.document-card:hover {
  border-color: var(--el-color-primary-light-7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-icon {
  font-size: 20px;
}

.status-icon.done {
  color: var(--el-color-success);
}

.status-icon.running {
  color: var(--el-color-primary);
}

.status-icon.pending {
  color: var(--el-color-warning);
}

.status-icon.failed {
  color: var(--el-color-danger);
}

.spinning {
  animation: rotate 1s linear infinite;
}

.card-body {
  margin-bottom: 12px;
}

.document-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.card-footer span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
```

**Step 2:** 提交

```bash
git add app/src/components/parse/ParseDocumentsView.vue
git commit -m "refactor: completely rewrite ParseDocumentsView.vue"
```

---

### Task 6: 简化 ParseDetailsDrawer.vue

**Files:**
- Modify: `app/src/components/parse/ParseDetailsDrawer.vue`

**Step 1:** 简化 ParseDetailsDrawer.vue，临时标记为开发中

```vue
<template>
  <el-drawer v-model="visible" title="解析详情" size="50%">
    <div class="parse-details-drawer">
      <el-alert type="info" show-icon>
        详情功能开发中...
      </el-alert>
    </div>
  </el-drawer>
</template>

<script setup>
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  filePath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:visible', 'close'])

function handleClose() {
  emit('update:visible', false)
  emit('close')
}
</script>

<style scoped>
.parse-details-drawer {
  padding: 16px;
}
</style>
```

**Step 2:** 提交

```bash
git add app/src/components/parse/ParseDetailsDrawer.vue
git commit -m "refactor: simplify ParseDetailsDrawer, mark as in development"
```

---

### Task 7: 完全重写 TextExtractor.js

**Files:**
- Modify: `app/src/processors/parse/TextExtractor.js`

**Step 1:** 完全重写 TextExtractor.js

```javascript
import { useParseStore } from '@/stores/parse'

export class TextExtractor {
  static async extract(filePath) {
    const parseStore = useParseStore()

    try {
      const duplicateCheck = await parseStore.checkDuplicate({ file_path: filePath })

      if (duplicateCheck.is_duplicate && duplicateCheck.existing_task) {
        const task = duplicateCheck.existing_task
        if (task.markdown_content) {
          return {
            success: true,
            markdown: task.markdown_content,
            taskId: task.id,
            isCached: true
          }
        } else {
          const result = await parseStore.getTaskResult(task.id)
          return {
            success: true,
            markdown: result.markdown_content,
            taskId: task.id,
            isCached: true
          }
        }
      }

      const task = await parseStore.parseLocalFile(filePath)

      if (task.is_duplicate) {
        if (task.markdown_content) {
          return {
            success: true,
            markdown: task.markdown_content,
            taskId: task.id,
            isCached: true
          }
        }
      }

      const pollResult = await parseStore.pollTaskUntilDone(task.id)
      if (pollResult.success) {
        const result = await parseStore.getTaskResult(task.id)
        return {
          success: true,
          markdown: result.markdown_content,
          taskId: task.id
        }
      } else {
        return {
          success: false,
          error: pollResult.error
        }
      }
    } catch (error) {
      console.error('文本提取失败:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }
}
```

**Step 2:** 提交

```bash
git add app/src/processors/parse/TextExtractor.js
git commit -m "refactor: completely rewrite TextExtractor to use new store"
```

---

## Phase 3: 测试与验证

### Task 8: 前端构建和测试

**Step 1:** 运行 lint 检查

```bash
cd app
npm run lint
```

**Step 2:** 修复 lint 错误（如有）

**Step 3:** 运行前端 build

```bash
npm run build
```

**Step 4:** 验证 build 成功

---

### Task 9: 集成测试

**测试场景：**
1. 访问解析管理页面
2. 查看统计数据显示
3. 查看任务队列（各标签页）
4. 查看已解析文档列表
5. 验证搜索和筛选功能
6. 验证刷新功能

---

## 总结

### 文件变更总览

**修改：**
- `app/src/stores/parse.js` - 完全重写
- `app/src/views/ParseManagement.vue` - 完全重写
- `app/src/components/parse/ParseStatsView.vue` - 完全重写
- `app/src/components/parse/ParseQueueView.vue` - 完全重写
- `app/src/components/parse/ParseDocumentsView.vue` - 完全重写
- `app/src/components/parse/ParseDetailsDrawer.vue` - 简化
- `app/src/processors/parse/TextExtractor.js` - 完全重写

**已删除：**
- `app/src/repositories/ParseIndexRepository.js`
- `app/src/repositories/IndexedDBRepository.js`

---

**Plan complete and saved to `docs/plans/2026-03-03-frontend-parse-refactor.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
