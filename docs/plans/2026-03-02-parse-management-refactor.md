# 文档解析管理重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将文档解析管理从左侧边栏标签页提取为独立的全屏页面，并全面增强用户体验。

**Architecture:** 创建类似设置页面的全屏解析管理页面，包含左侧功能导航和右侧内容区域；重构侧边栏移除标签页，添加永久入口按钮；增强现有解析功能组件以适应新布局。

**Tech Stack:** Vue 3, Element Plus, Pinia, Vue Router

---

## 实施概览

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 1. 基础设施 | 创建页面骨架和路由 | 15分钟 |
| 2. 核心组件 | 创建导航组件和主页面 | 20分钟 |
| 3. 功能迁移 | 重构现有解析组件 | 25分钟 |
| 4. UI 增强 | 添加批量操作和搜索过滤 | 20分钟 |
| 5. 侧边栏改造 | 移除标签页添加入口 | 15分钟 |
| 6. 测试验证 | 功能测试和回归测试 | 15分钟 |

---

## 详细任务清单

### Task 1: 更新路由配置

**Files:**
- Modify: `app/src/router/index.js`

**Step 1: 添加解析管理页面路由**

编辑 `app/src/router/index.js`，添加新路由：

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
  },
  {
    path: '/parse-management',
    name: 'parse-management',
    component: () => import('@/views/ParseManagement.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
```

**Step 2: 验证路由配置**

确认文件保存正确。

---

### Task 2: 创建解析管理侧边栏导航组件

**Files:**
- Create: `app/src/components/Layout/ParseSidebar.vue`

**Step 1: 创建 ParseSidebar 组件**

```vue
<template>
  <div class="parse-sidebar">
    <div
      v-for="item in navItems"
      :key="item.key"
      class="nav-item"
      :class="{ active: modelValue === item.key }"
      @click="$emit('update:modelValue', item.key)"
    >
      <el-icon><component :is="item.icon" /></el-icon>
      <span class="nav-label">{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { Document, List, TrendCharts } from '@element-plus/icons-vue'

defineProps({
  modelValue: {
    type: String,
    default: 'queue',
  },
})

defineEmits(['update:modelValue'])

const navItems = [
  { key: 'queue', label: '队列管理', icon: Document },
  { key: 'documents', label: '已解析文档', icon: List },
  { key: 'stats', label: '解析统计', icon: TrendCharts },
]
</script>

<style scoped>
.parse-sidebar {
  width: 200px;
  border-right: 1px solid var(--el-border-color);
  padding: 16px 0;
  background: var(--el-bg-color-page);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--el-text-color-regular);
}

.nav-item:hover {
  background: var(--el-fill-color-light);
}

.nav-item.active {
  background: var(--el-fill-color);
  color: var(--el-color-primary);
  font-weight: 500;
  border-right: 3px solid var(--el-color-primary);
}

.nav-label {
  font-size: 14px;
}
</style>
```

---

### Task 3: 创建解析管理主页面

**Files:**
- Create: `app/src/views/ParseManagement.vue`

**Step 1: 创建 ParseManagement 页面组件**

```vue
<template>
  <div class="parse-management-page">
    <header class="page-header">
      <el-button @click="handleBack" link>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="header-title">解析管理</div>
      <div class="header-actions">
        <el-button size="small" :loading="isParsing" @click="handleParseAll">
          开始全部解析
        </el-button>
        <el-button size="small" @click="handleExportAll" :disabled="stats.completed === 0">
          导出全部
        </el-button>
      </div>
    </header>
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
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import ParseSidebar from '@/components/Layout/ParseSidebar.vue'
import ParseQueueView from '@/components/parse/ParseQueueView.vue'
import ParseDocumentsView from '@/components/parse/ParseDocumentsView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'

const router = useRouter()
const parseStore = useParseStore()
const activeTab = ref('queue')
const isParsing = ref(false)

const stats = computed(() => parseStore.stats)

const componentMap = {
  queue: ParseQueueView,
  documents: ParseDocumentsView,
  stats: ParseStatsView,
}

const currentComponent = computed(() => componentMap[activeTab.value] || ParseQueueView)

function handleBack() {
  router.push('/')
}

async function handleParseAll() {
  const pending = Object.entries(parseStore.parseIndex)
    .filter(([, data]) => data.status === 'pending')
    .map(([filePath, data]) => ({ filePath, fileType: data.type || data.fileType }))

  if (pending.length === 0) {
    ElMessage.info('没有待解析的文件')
    return
  }

  isParsing.value = true
  try {
    ElMessage.info(`开始解析 ${pending.length} 个文件...`)
    await parseStore.startParseBatch(pending)
    ElMessage.success('批量解析完成')
  } catch (error) {
    ElMessage.error(`批量解析失败: ${error.message}`)
  } finally {
    isParsing.value = false
  }
}

function handleExportAll() {
  ElMessage.info('导出功能开发中')
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

---

### Task 4: 创建增强版队列管理视图

**Files:**
- Create: `app/src/components/parse/ParseQueueView.vue`

**Step 1: 创建增强版队列管理视图**

```vue
<template>
  <div class="parse-queue-view">
    <div class="view-header">
      <h2>队列管理</h2>
      <div class="header-actions">
        <el-button size="small" @click="handleClearCompleted">清除已完成</el-button>
        <el-button size="small" type="danger" @click="handleClearAll" :disabled="totalCount === 0">
          清空队列
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeQueueTab" class="queue-tabs">
      <el-tab-pane label="解析中" name="parsing">
        <FileList :files="parsingFiles" show-progress />
      </el-tab-pane>
      <el-tab-pane label="待解析" name="pending">
        <FileList :files="pendingFiles" show-actions @parse="handleParseFile" @remove="handleRemoveFile" />
      </el-tab-pane>
      <el-tab-pane label="失败" name="failed">
        <FileList :files="failedFiles" show-error show-actions @retry="handleRetryFile" @remove="handleRemoveFile" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useParseStore } from '@/stores/parse'
import FileList from './FileList.vue'

const parseStore = useParseStore()
const activeQueueTab = ref('parsing')

const pendingFiles = computed(() => parseStore.pendingFiles)
const parsingFiles = computed(() => parseStore.parsingFiles)
const failedFiles = computed(() => parseStore.failedFiles)

const totalCount = computed(() => 
  pendingFiles.value.length + parsingFiles.value.length + failedFiles.value.length
)

async function handleParseFile(file) {
  try {
    await parseStore.startParse(file.filePath, file.fileType)
    ElMessage.success('开始解析')
  } catch (error) {
    ElMessage.error(`解析失败: ${error.message}`)
  }
}

async function handleRetryFile(file) {
  try {
    await parseStore.startParse(file.filePath, file.fileType)
    ElMessage.success('开始重试')
  } catch (error) {
    ElMessage.error(`重试失败: ${error.message}`)
  }
}

function handleRemoveFile(file) {
  parseStore.removeFile(file.filePath)
  ElMessage.success('已移除')
}

function handleClearCompleted() {
  ElMessage.info('清除已完成功能开发中')
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm(
      '确定要清空整个队列吗？此操作不可恢复。',
      '清空队列',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    ElMessage.info('清空队列功能开发中')
  } catch {
    // 用户取消
  }
}
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
</style>
```

---

### Task 5: 创建通用文件列表组件

**Files:**
- Create: `app/src/components/parse/FileList.vue`

**Step 1: 创建 FileList 组件**

```vue
<template>
  <div class="file-list">
    <div v-if="files.length === 0" class="empty-state">
      <el-empty description="暂无文件" />
    </div>
    <div v-else class="file-items">
      <div
        v-for="file in files"
        :key="file.filePath"
        class="file-item"
        :class="{ failed: file.error }"
      >
        <el-checkbox v-if="showSelection" v-model="selectedFiles" :value="file.filePath" />
        <div class="file-icon">
          <el-icon v-if="!file.error"><Document /></el-icon>
          <el-icon v-else class="error-icon"><CircleClose /></el-icon>
        </div>
        <div class="file-info">
          <div class="file-name">{{ getFileName(file.filePath) }}</div>
          <div class="file-path" :title="file.filePath">{{ file.filePath }}</div>
          <div v-if="showProgress && file.progress !== undefined" class="file-progress">
            <el-progress :percentage="file.progress" :stroke-width="6" />
          </div>
          <div v-if="showError && file.error" class="file-error">
            <el-tag size="small" type="danger">{{ file.error }}</el-tag>
          </div>
        </div>
        <div v-if="show-actions" class="file-actions">
          <el-button v-if="!file.error" link type="primary" size="small" @click="$emit('parse', file)">
            解析
          </el-button>
          <el-button v-else link type="warning" size="small" @click="$emit('retry', file)">
            重试
          </el-button>
          <el-button link type="danger" size="small" @click="$emit('remove', file)">
            移除
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, CircleClose } from '@element-plus/icons-vue'

defineProps({
  files: { type: Array, default: () => [] },
  showSelection: { type: Boolean, default: false },
  showProgress: { type: Boolean, default: false },
  showError: { type: Boolean, default: false },
  showActions: { type: Boolean, default: false },
})

defineEmits(['parse', 'retry', 'remove'])

const selectedFiles = ref([])

function getFileName(filePath) {
  return filePath.split(/[\\/]/).pop() || filePath
}
</script>

<style scoped>
.file-list {
  height: 100%;
}

.empty-state {
  padding: 40px 0;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.file-item.failed {
  border-color: var(--el-color-danger-lighter);
  background: rgba(245, 108, 108, 0.05);
}

.file-icon {
  font-size: 24px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.error-icon {
  color: var(--el-color-danger);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.file-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 8px;
}

.file-progress {
  margin-top: 8px;
}

.file-error {
  margin-top: 8px;
}

.file-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
</style>
```

---

### Task 6: 创建已解析文档视图

**Files:**
- Create: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1: 创建已解析文档视图**

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
          <el-option label="已完成" value="completed" />
          <el-option label="解析中" value="parsing" />
          <el-option label="待解析" value="pending" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
    </div>

    <div v-if="filteredDocuments.length === 0" class="empty-state">
      <el-empty description="暂无解析文档" />
    </div>
    <div v-else class="document-grid">
      <div
        v-for="(data, filePath) in filteredDocuments"
        :key="filePath"
        class="document-card"
        @click="handleSelectDocument(filePath)"
      >
        <div class="card-header">
          <el-icon class="status-icon" :class="data.status">
            <CircleCheck v-if="data.status === 'completed'" />
            <Loading v-else-if="data.status === 'parsing'" class="spinning" />
            <Clock v-else-if="data.status === 'pending'" />
            <CircleClose v-else />
          </el-icon>
          <el-tag :type="getStatusType(data.status)" size="small">
            {{ getStatusLabel(data.status) }}
          </el-tag>
        </div>
        <div class="card-body">
          <div class="document-title">{{ getFileName(filePath) }}</div>
          <div class="document-path" :title="filePath">{{ filePath }}</div>
        </div>
        <div class="card-footer">
          <span class="file-type">{{ data.type || '未知' }}</span>
          <span v-if="data.duration" class="file-duration">
            {{ (data.duration / 1000).toFixed(1) }}s
          </span>
          <span v-if="data.size" class="file-size">{{ formatSize(data.size) }}</span>
        </div>
      </div>
    </div>

    <ParseDetailsDrawer
      v-model:visible="detailsVisible"
      :file-path="selectedFilePath"
      @close="detailsVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CircleCheck, Loading, Clock, CircleClose } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import ParseDetailsDrawer from './ParseDetailsDrawer.vue'

const parseStore = useParseStore()
const searchText = ref('')
const statusFilter = ref('')
const detailsVisible = ref(false)
const selectedFilePath = ref(null)

const filteredDocuments = computed(() => {
  const index = parseStore.parseIndex
  let result = { ...index }

  if (statusFilter.value) {
    result = Object.fromEntries(
      Object.entries(result).filter(([, data]) => data.status === statusFilter.value)
    )
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = Object.fromEntries(
      Object.entries(result).filter(([filePath]) =>
        filePath.toLowerCase().includes(search)
      )
    )
  }

  return result
})

function getFileName(filePath) {
  return filePath.split(/[\\/]/).pop() || filePath
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getStatusType(status) {
  const map = {
    completed: 'success',
    parsing: 'primary',
    pending: 'warning',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    completed: '已完成',
    parsing: '解析中',
    pending: '待解析',
    failed: '失败',
  }
  return map[status] || status
}

function handleSelectDocument(filePath) {
  selectedFilePath.value = filePath
  detailsVisible.value = true
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

.status-icon.completed {
  color: var(--el-color-success);
}

.status-icon.parsing {
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

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
```

---

### Task 7: 创建解析详情抽屉组件

**Files:**
- Create: `app/src/components/parse/ParseDetailsDrawer.vue`

**Step 1: 创建解析详情抽屉组件**

```vue
<template>
  <el-drawer
    v-model="visibleLocal"
    title="解析详情"
    size="50%"
    :destroy-on-close="true"
  >
    <div v-if="fileData" class="parse-details">
      <div class="detail-section">
        <h4>文件信息</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="文件路径">{{ filePath }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ fileData.type || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="解析状态">
            <el-tag :type="getStatusType(fileData.status)">
              {{ getStatusLabel(fileData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="fileData.duration" label="解析耗时">
            {{ (fileData.duration / 1000).toFixed(1) }} 秒
          </el-descriptions-item>
          <el-descriptions-item v-if="fileData.size" label="文件大小">
            {{ formatSize(fileData.size) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="fileData.error" label="错误信息">
            <span class="error-text">{{ fileData.error }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="fileData.status === 'completed' && fileData.textPreview" class="detail-section">
        <h4>文本预览</h4>
        <div class="text-preview">
          {{ fileData.textPreview }}
        </div>
      </div>

      <div class="detail-actions">
        <el-button v-if="fileData.status === 'failed'" type="primary" @click="handleReparse">
          重新解析
        </el-button>
        <el-button v-else-if="fileData.status === 'completed'" type="primary" @click="handleReparse">
          重新解析
        </el-button>
        <el-button v-if="fileData.status === 'completed'" @click="handleExport">
          导出文本
        </el-button>
        <el-button type="danger" @click="handleDelete">
          删除记录
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useParseStore } from '@/stores/parse'

const props = defineProps({
  visible: { type: Boolean, default: false },
  filePath: { type: String, default: null },
})

const emit = defineEmits(['update:visible', 'close'])

const parseStore = useParseStore()
const visibleLocal = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const fileData = computed(() => {
  if (!props.filePath) return null
  return parseStore.parseIndex[props.filePath] || null
})

watch(() => props.visible, (val) => {
  if (!val) emit('close')
})

function getStatusType(status) {
  const map = {
    completed: 'success',
    parsing: 'primary',
    pending: 'warning',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    completed: '已完成',
    parsing: '解析中',
    pending: '待解析',
    failed: '失败',
  }
  return map[status] || status
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function handleReparse() {
  if (!props.filePath || !fileData.value) return
  try {
    await parseStore.startParse(props.filePath, fileData.value.type || fileData.value.fileType)
    ElMessage.success('开始重新解析')
  } catch (error) {
    ElMessage.error(`解析失败: ${error.message}`)
  }
}

function handleExport() {
  ElMessage.info('导出功能开发中')
}

async function handleDelete() {
  if (!props.filePath) return
  try {
    await ElMessageBox.confirm(
      '确定要删除这条解析记录吗？',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    parseStore.removeFile(props.filePath)
    visibleLocal.value = false
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.parse-details {
  padding: 0 20px 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.text-preview {
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-text {
  color: var(--el-color-danger);
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
```

---

### Task 8: 创建解析统计视图

**Files:**
- Create: `app/src/components/parse/ParseStatsView.vue`

**Step 1: 创建解析统计视图**

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
          <div class="stat-value">{{ stats.completed }}</div>
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
          <el-button type="primary" :loading="isParsing" @click="handleParseAll">
            批量解析待处理文件
          </el-button>
          <el-button type="warning" :disabled="stats.failed === 0 || isParsing" @click="handleRetryFailed">
            重试失败文件
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
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, CircleCheck, Clock, CircleClose } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'

const parseStore = useParseStore()
const isParsing = ref(false)

const stats = computed(() => parseStore.stats)

const distributionData = computed(() => {
  const total = stats.value.total || 0
  const items = [
    { status: 'completed', label: '已完成', count: stats.value.completed },
    { status: 'pending', label: '待解析', count: stats.value.pending },
    { status: 'parsing', label: '解析中', count: stats.value.parsing },
    { status: 'failed', label: '失败', count: stats.value.failed },
  ]
  return items.map(item => ({
    ...item,
    percentage: total > 0 ? (item.count / total) * 100 : 0,
  }))
})

async function handleParseAll() {
  const pending = Object.entries(parseStore.parseIndex)
    .filter(([, data]) => data.status === 'pending')
    .map(([filePath, data]) => ({ filePath, fileType: data.type || data.fileType }))

  if (pending.length === 0) {
    ElMessage.info('没有待解析的文件')
    return
  }

  isParsing.value = true
  try {
    ElMessage.info(`开始解析 ${pending.length} 个文件...`)
    await parseStore.startParseBatch(pending)
    ElMessage.success('批量解析完成')
  } catch (error) {
    ElMessage.error(`批量解析失败: ${error.message}`)
  } finally {
    isParsing.value = false
  }
}

function handleRetryFailed() {
  parseStore.retryFailed()
  ElMessage.info('已开始重试失败任务')
}
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

.distribution-segment.completed {
  background: var(--el-color-success);
}

.distribution-segment.pending {
  background: var(--el-color-warning);
}

.distribution-segment.parsing {
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

.legend-dot.completed {
  background: var(--el-color-success);
}

.legend-dot.pending {
  background: var(--el-color-warning);
}

.legend-dot.parsing {
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

---

### Task 9: 重构左侧边栏 - 移除标签页添加入口

**Files:**
- Modify: `app/src/components/Layout/Sidebar.vue`

**Step 1: 重构 Sidebar 组件**

替换整个 `Sidebar.vue` 内容：

```vue
<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <span class="workspace-title">工作区</span>
      <div class="header-actions">
        <el-button :loading="isRefreshing" link type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>
    
    <div class="file-tree-container">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        lazy
        :load="loadNode"
        node-key="id"
        default-expand-all
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
        :highlight-current="true"
      />
    </div>

    <div class="sidebar-footer">
      <el-button type="primary" class="parse-management-btn" @click="goToParseManagement">
        <el-icon><Document /></el-icon>
        <span>解析管理</span>
      </el-button>
    </div>

    <teleport to="body">
      <div v-if="contextMenu.visible" class="context-menu" :style="contextMenu.style" @click.stop>
        <div
          v-if="contextMenu.nodeData?.type === 'file'"
          class="context-menu-item"
          @click="handleAddToParse"
        >
          添加到解析
        </div>
        <div
          v-if="
            contextMenu.nodeData?.type === 'folder' &&
            workspaceStore.folders.some((f) => f.id === contextMenu.nodeData?.id)
          "
          class="context-menu-item"
          @click="handleRemoveFolder"
        >
          移除文件夹
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Document } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useWorkspaceStore } from '@/stores/workspace'
import { useDocumentStore } from '@/stores/document'
import { useParseStore } from '@/stores/parse'

const router = useRouter()

function getFileType(fileName) {
  const ext = fileName.split('.').pop().toLowerCase()
  if (ext === 'md') return 'markdown'
  if (ext === 'pdf') return 'pdf'
  if (['mp3', 'wav', 'ogg', 'm4a', 'flac'].includes(ext)) return 'audio'
  if (['mp4', 'webm', 'mov', 'mkv'].includes(ext)) return 'video'
  return 'unknown'
}

const workspaceStore = useWorkspaceStore()
const documentStore = useDocumentStore()
const parseStore = useParseStore()

const treeProps = {
  children: 'children',
  label: 'name',
}

const treeData = ref([])
const treeRef = ref(null)
const isRefreshing = ref(false)

const contextMenu = ref({
  visible: false,
  style: { left: '0px', top: '0px' },
  nodeData: null,
})

async function loadNode(node, resolve) {
  if (node.level === 0) {
    return resolve([])
  }

  const nodeData = node.data
  if (nodeData.type === 'file') {
    return resolve([])
  }

  try {
    const result = await window.electronAPI.readDir(nodeData.path)
    if (result.success) {
      const children = [
        ...result.folders.map((f) => ({ ...f, leaf: false, loaded: false })),
        ...result.files.map((f) => ({ ...f, leaf: true })),
      ]
      return resolve(children)
    }
    return resolve([])
  } catch (error) {
    console.error('加载文件夹失败:', error)
    return resolve([])
  }
}

function initTreeData() {
  treeData.value = workspaceStore.folders.map((f) => ({
    ...f,
    leaf: false,
    loaded: false,
  }))
}

function handleContextMenu(event, data) {
  if (
    data.type === 'file' ||
    (data.type === 'folder' && workspaceStore.folders.some((f) => f.id === data.id))
  ) {
    event.preventDefault()
    event.stopPropagation()
    contextMenu.value = {
      visible: true,
      style: { left: `${event.clientX}px`, top: `${event.clientY}px` },
      nodeData: data,
    }
  }
}

function handleAddToParse() {
  contextMenu.value.visible = false
  const data = contextMenu.value.nodeData
  if (!data || data.type !== 'file') return

  const fileType = getFileType(data.name)
  if (fileType !== 'markdown' && fileType !== 'pdf') {
    ElMessage.warning('仅支持 Markdown 和 PDF 文件')
    return
  }

  parseStore.addFile(data.path, fileType)
  ElMessage.success('已添加到解析队列')
}

function handleClickOutside() {
  contextMenu.value.visible = false
}

async function handleRemoveFolder() {
  contextMenu.value.visible = false
  try {
    await ElMessageBox.confirm(
      `确定要移除文件夹「${contextMenu.value.nodeData.name}」吗？`,
      '移除文件夹',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    workspaceStore.removeFolder(contextMenu.value.nodeData.id)
  } catch {
    // 用户取消操作，忽略错误
  }
}

async function handleRefresh() {
  isRefreshing.value = true
  try {
    initTreeData()
  } finally {
    isRefreshing.value = false
  }
}

function handleNodeClick(data) {
  if (data.type === 'file') {
    workspaceStore.selectFile(data.id)
    documentStore.loadFile(data)
  }
}

function goToParseManagement() {
  router.push('/parse-management')
}

watch(
  () => workspaceStore.folders,
  () => {
    initTreeData()
  },
  { deep: true },
)

onMounted(() => {
  initTreeData()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.sidebar {
  width: 25%;
  min-width: 200px;
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.workspace-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.file-tree-container {
  flex: 1;
  overflow-y: auto;
}

.file-tree-container :deep(.el-tree) {
  border: none;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.parse-management-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.context-menu {
  position: fixed;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 3000;
  min-width: 120px;
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.context-menu-item:hover {
  background: var(--el-fill-color-light);
}
</style>
```

---

### Task 10: 验证功能完整性

**测试步骤：**

1. **启动应用**
   ```bash
   cd app
   npm run dev
   ```

2. **测试路由导航**
   - 访问主页，点击左侧边栏底部的"解析管理"按钮
   - 验证跳转到 `/parse-management` 页面
   - 验证顶部返回按钮能回到主页

3. **测试队列管理**
   - 从文件树右键添加文件到解析
   - 验证文件出现在"待解析"标签页
   - 测试"开始全部解析"按钮

4. **测试已解析文档**
   - 添加搜索关键词测试过滤
   - 使用状态筛选器测试过滤
   - 点击文档卡片打开详情抽屉

5. **测试统计页面**
   - 验证统计卡片显示正确数据
   - 验证状态分布条
   - 测试快速操作按钮

6. **回归测试**
   - 验证文件树功能正常
   - 验证文件查看功能正常
   - 验证设置页面正常

---

## 项目文件结构变更总结

### 新增文件
```
app/src/
├── views/
│   └── ParseManagement.vue          # 解析管理主页面
├── components/
│   ├── Layout/
│   │   └── ParseSidebar.vue         # 解析管理侧边栏导航
│   └── parse/
│       ├── ParseQueueView.vue        # 队列管理视图
│       ├── ParseDocumentsView.vue    # 已解析文档视图
│       ├── ParseStatsView.vue        # 解析统计视图
│       ├── FileList.vue              # 通用文件列表组件
│       └── ParseDetailsDrawer.vue    # 解析详情抽屉
```

### 修改文件
```
app/src/
├── router/index.js                    # 添加解析管理路由
└── components/Layout/Sidebar.vue     # 重构侧边栏
```

---

## 增强功能清单

✅ 全屏独立页面布局  
✅ 左侧功能导航（队列/文档/统计）  
✅ 队列管理标签页（解析中/待解析/失败）  
✅ 已解析文档搜索和筛选  
✅ 文档卡片网格布局  
✅ 解析详情抽屉  
✅ 可视化状态分布  
✅ 统计卡片面板  
✅ 侧边栏永久入口按钮  

---

**Plan complete and saved to `docs/plans/2026-03-02-parse-management-refactor.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
