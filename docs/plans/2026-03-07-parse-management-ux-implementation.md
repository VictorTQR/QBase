# 解析管理 UI/UX 重构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将解析管理页面重构为新的UI/UX设计，包括顶部标签页、4阶段流水线步骤条、正交筛选器、批量操作复选框、增强版抽屉等。

**Architecture:**
1. 保留现有 stores (parse.js, vector.js) 不变
2. 重构 ParseManagement.vue 主页面，移除侧边栏，添加顶部标签页
3. 创建新组件：FileManagementView.vue, KanbanView.vue, ChunkDetailsDrawer.vue
4. 保留并增强现有组件：ParseStatsView.vue
5. 渐进式迁移，保留旧组件作为备份

**Tech Stack:** Vue 3, Element Plus, Pinia, Vite

---

## 前置准备

### Task 0: 创建备份分支和备份文件

**Files:**
- Git操作：创建备份分支

**Step 1: 创建备份分支**
```bash
git checkout -b backup/parse-management-original
git checkout main
```

**Step 2: 备份现有组件**
```bash
cd app/src
cp views/ParseManagement.vue views/ParseManagement.vue.backup
cp components/Layout/ParseSidebar.vue components/Layout/ParseSidebar.vue.backup
cp -r components/parse components/parse.backup
```

**Step 3: 提交备份**
```bash
git add views/ParseManagement.vue.backup components/Layout/ParseSidebar.vue.backup components/parse.backup/
git commit -m "backup: 保存解析管理原始代码"
```

---

## 第一阶段：创建新组件

### Task 1: 创建 FileManagementView.vue - 文件管理表格视图

**Files:**
- Create: `app/src/components/parse/FileManagementView.vue`

**Step 1: 创建组件基础结构**
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import { ElMessage, ElCheckbox } from 'element-plus'

const parseStore = useParseStore()
const vectorStore = useVectorStore()

// 状态
const selectedFiles = ref(new Set())
const selectAll = ref(false)
const fileTypeFilter = ref('')
const statusFilter = ref('')
const searchText = ref('')

// 抽屉
const drawerVisible = ref(false)
const selectedFile = ref(null)

// 筛选后的文件列表
const mergedFiles = computed(() => {
  const tasks = parseStore.tasks
  return tasks.map(task => {
    const isIndexed = vectorStore.isFileIndexed(task.file_path)
    const indexedFile = vectorStore.indexedFilesList?.find(
      f => f.file_path === task.file_path
    )
    
    return {
      ...task,
      vectorIndexed: isIndexed,
      chunkCount: indexedFile?.chunk_count || 0
    }
  })
})

const filteredFiles = computed(() => {
  let files = mergedFiles.value
  
  // 搜索过滤
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    files = files.filter(f => 
      f.file_name.toLowerCase().includes(search) ||
      f.file_path?.toLowerCase().includes(search)
    )
  }
  
  // 文件类型过滤
  if (fileTypeFilter.value) {
    // 根据文件扩展名或parser_type过滤
    files = files.filter(f => {
      if (fileTypeFilter.value === 'document') {
        return f.parser_type === 'mineru' || f.file_name?.endsWith('.md')
      } else if (fileTypeFilter.value === 'audio') {
        return f.parser_type === 'audio'
      }
      return true
    })
  }
  
  // 状态过滤（简化版，后续完善）
  if (statusFilter.value) {
    files = files.filter(f => {
      if (statusFilter.value === 'pending') {
        return f.state === 'pending'
      } else if (statusFilter.value === 'running') {
        return f.state === 'running' || vectorStore.isIndexing
      } else if (statusFilter.value === 'completed') {
        return f.state === 'done' && f.vectorIndexed
      } else if (statusFilter.value === 'failed') {
        return f.state === 'failed'
      }
      return true
    })
  }
  
  return files
})

// 批量操作
function toggleSelectAll() {
  if (selectAll.value) {
    selectedFiles.value = new Set(filteredFiles.value.map(f => f.id))
  } else {
    selectedFiles.value.clear()
  }
}

function toggleFileSelection(fileId) {
  if (selectedFiles.value.has(fileId)) {
    selectedFiles.value.delete(fileId)
  } else {
    selectedFiles.value.add(fileId)
  }
  selectAll.value = selectedFiles.value.size === filteredFiles.value.length
}

// 键盘快捷键
onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

function handleKeyDown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
    e.preventDefault()
    selectAll.value = true
    toggleSelectAll()
  }
}

// 打开抽屉
function openDrawer(file) {
  selectedFile.value = file
  drawerVisible.value = true
}

// 加载数据
onMounted(async () => {
  try {
    await Promise.all([
      parseStore.fetchTasks(),
      parseStore.fetchStats(),
      vectorStore.loadStats(),
      vectorStore.loadIndexedFiles()
    ])
  } catch (err) {
    console.error('加载数据失败:', err)
  }
})
</script>

<template>
  <div class="file-management-view">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">类型:</span>
        <el-select v-model="fileTypeFilter" placeholder="全部" clearable style="width: 120px">
          <el-option label="文档" value="document" />
          <el-option label="音频" value="audio" />
        </el-select>
      </div>
      <div class="filter-group">
        <span class="filter-label">状态:</span>
        <el-select v-model="statusFilter" placeholder="全部" clearable style="width: 120px">
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
      <el-input
        v-model="searchText"
        placeholder="搜索文件名或路径..."
        prefix-icon="Search"
        style="width: 280px; margin-left: auto"
        clearable
      />
    </div>

    <!-- 批量操作条 -->
    <div v-if="selectedFiles.size > 0" class="batch-action-bar">
      <div class="batch-info">
        <span class="batch-count">{{ selectedFiles.size }}</span>
        <span>个文件已选中</span>
      </div>
      <div class="batch-buttons">
        <el-button type="primary" size="small">批量解析</el-button>
        <el-button size="small">批量索引</el-button>
        <el-button type="danger" size="small">删除</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <el-table :data="filteredFiles" style="width: 100%">
        <!-- 复选框列 -->
        <el-table-column width="55">
          <template #header>
            <el-checkbox v-model="selectAll" @change="toggleSelectAll" />
          </template>
          <template #default="{ row }">
            <el-checkbox
              :model-value="selectedFiles.has(row.id)"
              @change="() => toggleFileSelection(row.id)"
            />
          </template>
        </el-table-column>

        <!-- 文件名列 -->
        <el-table-column label="文件名" width="35%">
          <template #default="{ row }">
            <div class="file-cell">
              <div class="file-icon" :class="getFileIconClass(row)">
                {{ getFileIcon(row) }}
              </div>
              <div class="file-info">
                <div class="file-name">{{ row.file_name }}</div>
                <div class="file-path">{{ row.file_path || '未知路径' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 处理阶段列 -->
        <el-table-column label="处理阶段 (上传→解析→索引→完成)" width="28%">
          <template #default="{ row }">
            <div class="pipeline-stepper">
              <!-- 阶段1: 上传 -->
              <div class="step">
                <div class="step-icon success">✓</div>
              </div>
              <div class="step-connector" :class="{ completed: row.state !== 'pending' }"></div>
              
              <!-- 阶段2: 解析 -->
              <div class="step">
                <div
                  class="step-icon"
                  :class="getParseStageClass(row)"
                >
                  {{ getParseStageIcon(row) }}
                </div>
              </div>
              <div
                class="step-connector"
                :class="{ completed: row.state === 'done' }"
              ></div>
              
              <!-- 阶段3: 索引 -->
              <div class="step">
                <div
                  class="step-icon"
                  :class="getIndexStageClass(row)"
                >
                  {{ getIndexStageIcon(row) }}
                </div>
              </div>
              <div
                class="step-connector"
                :class="{ completed: row.vectorIndexed }"
              ></div>
              
              <!-- 阶段4: 完成 -->
              <div class="step">
                <div
                  class="step-icon"
                  :class="row.vectorIndexed ? 'success' : 'pending'"
                >
                  {{ row.vectorIndexed ? '✓' : '○' }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 文件信息列 -->
        <el-table-column label="文件信息" width="20%">
          <template #default="{ row }">
            <div class="stats-cell">
              <div class="stat-item">
                <span class="stat-label">{{ getFileInfoLabel1(row) }}</span>
                <span class="stat-value">{{ getFileInfoValue1(row) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">分块</span>
                <span class="stat-value">{{ row.chunkCount || '-' }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Token</span>
                <span class="stat-value">-</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="17%">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="openDrawer(row)">
                详情
              </el-button>
              <el-button v-if="row.state === 'failed'" size="small">
                重试
              </el-button>
              <el-button
                v-if="row.state === 'done' && !row.vectorIndexed"
                type="primary"
                size="small"
              >
                索引
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 抽屉（先用占位符，后续替换为真实组件） -->
    <el-drawer
      v-model="drawerVisible"
      title="文件详情"
      size="520px"
    >
      <div v-if="selectedFile">
        <p>文件名: {{ selectedFile.file_name }}</p>
        <p>路径: {{ selectedFile.file_path }}</p>
        <p>状态: {{ selectedFile.state }}</p>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.file-management-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.batch-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  background: #eef2ff;
  border-bottom: 1px solid #c7d2fe;
  margin: 0 -20px;
  padding: 10px 20px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-count {
  font-weight: 600;
  color: #4f46e5;
}

.batch-buttons {
  display: flex;
  gap: 10px;
}

.table-container {
  flex: 1;
  overflow: auto;
  padding-top: 16px;
}

.file-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: var(--el-fill-color-lighter);
  flex-shrink: 0;
}

.file-icon.pdf {
  background: #fef2f2;
  color: #dc2626;
}

.file-icon.md {
  background: #f0f9ff;
  color: #0284c7;
}

.file-icon.audio {
  background: #f0fdf4;
  color: #16a34a;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.file-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 280px;
}

.pipeline-stepper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.step {
  display: flex;
  align-items: center;
  gap: 4px;
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s;
}

.step-icon.pending {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-placeholder);
  border: 2px solid var(--el-border-color-lighter);
}

.step-icon.skipped {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-placeholder);
}

.step-icon.running {
  background: #4f46e5;
  color: white;
  animation: pulse 2s infinite;
}

.step-icon.success {
  background: #10b981;
  color: white;
}

.step-icon.failed {
  background: #ef4444;
  color: white;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 6px rgba(79, 70, 229, 0);
  }
}

.step-connector {
  width: 16px;
  height: 2px;
  background: var(--el-border-color-lighter);
}

.step-connector.completed {
  background: #10b981;
}

.stats-cell {
  display: flex;
  gap: 16px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.stat-value {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
```

**Step 2: 添加辅助方法**
```javascript
// 在 script setup 中添加

function getFileIconClass(row) {
  if (row.parser_type === 'audio') return 'audio'
  if (row.file_name?.endsWith('.md')) return 'md'
  return 'pdf'
}

function getFileIcon(row) {
  if (row.parser_type === 'audio') return '🎵'
  if (row.file_name?.endsWith('.md')) return '📝'
  return '📄'
}

function getParseStageClass(row) {
  if (row.state === 'done') return 'success'
  if (row.state === 'running') return 'running'
  if (row.state === 'failed') return 'failed'
  return 'pending'
}

function getParseStageIcon(row) {
  if (row.state === 'done') return '✓'
  if (row.state === 'running') return '●'
  if (row.state === 'failed') return '✕'
  return '○'
}

function getIndexStageClass(row) {
  if (row.state !== 'done') return 'pending'
  if (row.vectorIndexed) return 'success'
  if (vectorStore.isIndexing && vectorStore.currentIndexingFile === row.file_name) {
    return 'running'
  }
  return 'pending'
}

function getIndexStageIcon(row) {
  if (row.state !== 'done') return '○'
  if (row.vectorIndexed) return '✓'
  if (vectorStore.isIndexing && vectorStore.currentIndexingFile === row.file_name) {
    return '●'
  }
  return '○'
}

function getFileInfoLabel1(row) {
  if (row.parser_type === 'audio') return '时长'
  return '页数'
}

function getFileInfoValue1(row) {
  // TODO: 从元数据中获取页数或时长
  return '-'
}
```

**Step 3: 运行检查**
- 确保组件语法正确
- 检查导入路径正确

**Step 4: 提交**
```bash
git add app/src/components/parse/FileManagementView.vue
git commit -m "feat: 添加FileManagementView组件基础结构"
```

---

### Task 2: 创建 KanbanView.vue - 看板视图

**Files:**
- Create: `app/src/components/parse/KanbanView.vue`

**Step 1: 创建看板组件基础**
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'

const parseStore = useParseStore()
const vectorStore = useVectorStore()

const drawerVisible = ref(false)
const selectedFile = ref(null)

// 合并文件数据
const mergedFiles = computed(() => {
  const tasks = parseStore.tasks
  return tasks.map(task => {
    const isIndexed = vectorStore.isFileIndexed(task.file_path)
    return {
      ...task,
      vectorIndexed: isIndexed,
      kanbanColumn: getKanbanColumn(task, isIndexed)
    }
  })
})

function getKanbanColumn(task, isIndexed) {
  if (task.state === 'failed') return 'failed'
  if (task.state === 'pending') return 'pending'
  if (task.state === 'running') return 'running'
  if (task.state === 'done') {
    if (vectorStore.isIndexing && vectorStore.currentIndexingFile === task.file_name) {
      return 'running'
    }
    if (isIndexed) return 'completed'
    return 'running'
  }
  return 'pending'
}

const pendingFiles = computed(() => 
  mergedFiles.value.filter(f => f.kanbanColumn === 'pending')
)
const runningFiles = computed(() => 
  mergedFiles.value.filter(f => f.kanbanColumn === 'running')
)
const completedFiles = computed(() => 
  mergedFiles.value.filter(f => f.kanbanColumn === 'completed')
)
const failedFiles = computed(() => 
  mergedFiles.value.filter(f => f.kanbanColumn === 'failed')
)

function openDrawer(file) {
  selectedFile.value = file
  drawerVisible.value = true
}

onMounted(async () => {
  try {
    await Promise.all([
      parseStore.fetchTasks(),
      vectorStore.loadIndexedFiles()
    ])
  } catch (err) {
    console.error('加载数据失败:', err)
  }
})
</script>

<template>
  <div class="kanban-view">
    <div class="kanban-container">
      <!-- 待处理列 -->
      <div class="kanban-column">
        <div class="kanban-header">
          <div class="kanban-title">
            ⏸ 待处理
            <span class="kanban-count">{{ pendingFiles.length }}</span>
          </div>
        </div>
        <div class="kanban-cards">
          <div
            v-for="file in pendingFiles"
            :key="file.id"
            class="kanban-card"
            @click="openDrawer(file)"
          >
            <div class="card-header">
              <div class="card-icon" :class="getCardIconClass(file)">
                {{ getCardIcon(file) }}
              </div>
              <div style="flex: 1; min-width: 0">
                <div class="card-title">{{ file.file_name }}</div>
                <div class="card-path">{{ file.file_path }}</div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-tags"></div>
              <el-button type="primary" size="small" style="padding: 4px 10px; font-size: 12px">
                开始
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 处理中列 -->
      <div class="kanban-column">
        <div class="kanban-header">
          <div class="kanban-title">
            🔄 处理中
            <span class="kanban-count">{{ runningFiles.length }}</span>
          </div>
        </div>
        <div class="kanban-cards">
          <div
            v-for="file in runningFiles"
            :key="file.id"
            class="kanban-card"
            @click="openDrawer(file)"
          >
            <div class="card-header">
              <div class="card-icon" :class="getCardIconClass(file)">
                {{ getCardIcon(file) }}
              </div>
              <div style="flex: 1; min-width: 0">
                <div class="card-title">{{ file.file_name }}</div>
                <div class="card-path">{{ file.file_path }}</div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-tags"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 已完成列 -->
      <div class="kanban-column">
        <div class="kanban-header">
          <div class="kanban-title">
            ✅ 已完成
            <span class="kanban-count">{{ completedFiles.length }}</span>
          </div>
        </div>
        <div class="kanban-cards">
          <div
            v-for="file in completedFiles"
            :key="file.id"
            class="kanban-card"
            style="border-left: 3px solid #10b981"
            @click="openDrawer(file)"
          >
            <div class="card-header">
              <div class="card-icon" :class="getCardIconClass(file)">
                {{ getCardIcon(file) }}
              </div>
              <div style="flex: 1; min-width: 0">
                <div class="card-title">{{ file.file_name }}</div>
                <div class="card-path">{{ file.file_path }}</div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-tags">
                <span class="card-tag chunks">TODO 分块数</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 失败列 -->
      <div class="kanban-column">
        <div class="kanban-header">
          <div class="kanban-title" style="color: #ef4444">
            ❌ 失败
            <span class="kanban-count">{{ failedFiles.length }}</span>
          </div>
        </div>
        <div class="kanban-cards">
          <div
            v-for="file in failedFiles"
            :key="file.id"
            class="kanban-card failed"
            @click="openDrawer(file)"
          >
            <div class="card-header">
              <div class="card-icon" :class="getCardIconClass(file)">
                {{ getCardIcon(file) }}
              </div>
              <div style="flex: 1; min-width: 0">
                <div class="card-title">{{ file.file_name }}</div>
                <div class="card-path">{{ file.file_path }}</div>
              </div>
            </div>
            <div v-if="file.error_msg" style="font-size: 12px; color: #ef4444; margin-top: 8px">
              {{ file.error_msg }}
            </div>
            <div class="card-footer">
              <div class="card-tags"></div>
              <div style="display: flex; gap: 6px">
                <el-button type="primary" size="small" style="padding: 4px 10px; font-size: 12px">
                  重试
                </el-button>
                <el-button type="danger" size="small" style="padding: 4px 10px; font-size: 12px">
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 抽屉占位符 -->
    <el-drawer
      v-model="drawerVisible"
      title="文件详情"
      size="520px"
    >
      <div v-if="selectedFile">
        <p>文件名: {{ selectedFile.file_name }}</p>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
// 辅助方法
function getCardIconClass(file) {
  if (file.parser_type === 'audio') return 'audio'
  if (file.file_name?.endsWith('.md')) return 'md'
  return 'pdf'
}

function getCardIcon(file) {
  if (file.parser_type === 'audio') return '🎵'
  if (file.file_name?.endsWith('.md')) return '📝'
  return '📄'
}
</script>

<style scoped>
.kanban-view {
  height: 100%;
  overflow: auto;
  padding: 16px 0;
}

.kanban-container {
  display: flex;
  gap: 20px;
  min-width: max-content;
}

.kanban-column {
  flex: 1;
  min-width: 280px;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  padding: 16px;
}

.kanban-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.kanban-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.kanban-count {
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.kanban-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kanban-card {
  background: var(--el-bg-color);
  border-radius: 10px;
  padding: 14px;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.kanban-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.kanban-card.failed {
  border-left: 3px solid #ef4444;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.card-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  background: var(--el-fill-color-lighter);
}

.card-icon.pdf {
  background: #fef2f2;
  color: #dc2626;
}

.card-icon.md {
  background: #f0f9ff;
  color: #0284c7;
}

.card-icon.audio {
  background: #f0fdf4;
  color: #16a34a;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.card-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.card-tags {
  display: flex;
  gap: 6px;
}

.card-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.card-tag.chunks {
  background: #f0f9ff;
  color: #0369a1;
}
</style>
```

**Step 2: 提交**
```bash
git add app/src/components/parse/KanbanView.vue
git commit -m "feat: 添加KanbanView看板视图组件"
```

---

### Task 3: 创建增强版 ChunkDetailsDrawer.vue - 分块详情抽屉

**Files:**
- Create: `app/src/components/parse/ChunkDetailsDrawer.vue`

**Step 1: 创建抽屉组件**
```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  file: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'close'])

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

// 模拟分块数据（后续从store获取）
const chunks = computed(() => [
  { id: 1, preview: '第一章 引言 深度学习是机器学习的一个分支...', tokens: 384, status: 'done' },
  { id: 2, preview: '1.1 什么是神经网络 人工神经网络是受生物...', tokens: 412, status: 'done' },
  { id: 3, preview: '1.2 历史背景 深度学习的历史可以追溯到...', tokens: 356, status: 'running' },
  { id: 4, preview: '1.3 应用场景 深度学习在计算机视觉、自然...', tokens: 298, status: 'pending' },
  { id: 5, preview: '第二章 神经网络基础 本章介绍神经网络的基...', tokens: 421, status: 'pending' }
])
</script>

<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="(v) => emit('update:visible', v)"
    size="520px"
    @close="handleClose"
  >
    <template #header>
      <div class="drawer-header">
        <div class="drawer-title">
          <div class="drawer-file-icon" :class="getFileIconClass(file)">
            {{ getFileIcon(file) }}
          </div>
          <div class="drawer-file-info">
            <div class="drawer-file-name">{{ file?.file_name }}</div>
            <div class="drawer-file-meta">
              <span>2.5 MB</span>
              <span>·</span>
              <span>15 分块</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div class="drawer-content" v-if="file">
      <!-- 错误详情区域（条件显示） -->
      <div v-if="file.state === 'failed'" class="error-section">
        <div class="error-header">
          <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span class="error-title">处理失败</span>
        </div>
        <div class="error-message">{{ file.error_msg || '未知错误' }}</div>
        <div class="error-suggestion">建议：检查文件格式是否正确，或尝试重新上传。</div>
        <div class="error-actions">
          <el-button type="primary" size="small">查看日志</el-button>
          <el-button size="small">忽略</el-button>
        </div>
      </div>

      <!-- 可视化时间轴 -->
      <div class="drawer-pipeline">
        <div class="drawer-pipeline-title">处理时间轴</div>
        <div class="drawer-stepper">
          <div class="drawer-step">
            <div class="drawer-step-icon success">✓</div>
            <span class="drawer-step-label">上传</span>
            <span class="drawer-step-time">14:30:00</span>
          </div>
          <div class="drawer-step-connector completed"></div>
          <div class="drawer-step">
            <div class="drawer-step-icon" :class="getParseStageClass(file)">
              {{ getParseStageIcon(file) }}
            </div>
            <span class="drawer-step-label">解析</span>
            <span class="drawer-step-time">{{ getParseStageTime(file) }}</span>
          </div>
          <div class="drawer-step-connector" :class="{ completed: file.state === 'done' }"></div>
          <div class="drawer-step">
            <div class="drawer-step-icon" :class="getIndexStageClass(file)">
              {{ getIndexStageIcon(file) }}
            </div>
            <span class="drawer-step-label">索引</span>
            <span class="drawer-step-time">{{ getIndexStageTime(file) }}</span>
          </div>
          <div class="drawer-step-connector" :class="{ completed: isFileIndexed(file) }"></div>
          <div class="drawer-step">
            <div class="drawer-step-icon" :class="isFileIndexed(file) ? 'success' : 'pending'">
              {{ isFileIndexed(file) ? '✓' : '○' }}
            </div>
            <span class="drawer-step-label">完成</span>
            <span class="drawer-step-time">{{ isFileIndexed(file) ? '14:35:00' : '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 文件信息网格 -->
      <div class="info-section">
        <div class="section-title">文件信息</div>
        <div class="info-grid">
          <div class="info-row">
            <div class="info-label">路径</div>
            <div class="info-value">{{ file.file_path || '未知' }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">大小</div>
            <div class="info-value">2.5 MB</div>
          </div>
          <div class="info-row">
            <div class="info-label">页数</div>
            <div class="info-value">156</div>
          </div>
          <div class="info-row">
            <div class="info-label">解析时间</div>
            <div class="info-value">{{ formatDate(file.created_at) }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">分块数</div>
            <div class="info-value">15</div>
          </div>
          <div class="info-row">
            <div class="info-label">Token 数</div>
            <div class="info-value">4.8k</div>
          </div>
        </div>
      </div>

      <!-- 操作按钮区 -->
      <div class="info-section">
        <div class="section-title">操作</div>
        <div class="drawer-actions">
          <el-button>重新处理</el-button>
          <el-button type="primary">仅重新索引</el-button>
          <el-button type="danger">删除</el-button>
        </div>
        <div class="action-hint">快捷键: R-重试 P-暂停 D-删除</div>
      </div>

      <!-- 分块列表 -->
      <div class="info-section">
        <div class="section-title">分块列表</div>
        <div class="chunk-table-container">
          <el-table :data="chunks" style="width: 100%">
            <el-table-column label="#" width="50" />
            <el-table-column label="内容预览" />
            <el-table-column label="Token" width="80" />
            <el-table-column label="状态" width="90" />
            <el-table-column label="操作" width="70" />
          </el-table>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
// 辅助方法
import { useVectorStore } from '@/stores/vector'
const vectorStore = useVectorStore()

function getFileIconClass(file) {
  if (!file) return ''
  if (file.parser_type === 'audio') return 'audio'
  if (file.file_name?.endsWith('.md')) return 'md'
  return 'pdf'
}

function getFileIcon(file) {
  if (!file) return '📄'
  if (file.parser_type === 'audio') return '🎵'
  if (file.file_name?.endsWith('.md')) return '📝'
  return '📄'
}

function getParseStageClass(file) {
  if (!file) return 'pending'
  if (file.state === 'done') return 'success'
  if (file.state === 'running') return 'running'
  if (file.state === 'failed') return 'failed'
  return 'pending'
}

function getParseStageIcon(file) {
  if (!file) return '○'
  if (file.state === 'done') return '✓'
  if (file.state === 'running') return '●'
  if (file.state === 'failed') return '✕'
  return '○'
}

function getParseStageTime(file) {
  if (!file) return '-'
  if (file.state === 'done' || file.state === 'failed') {
    return formatDate(file.updated_at)
  }
  if (file.state === 'running') return '进行中...'
  return '-'
}

function getIndexStageClass(file) {
  if (!file || file.state !== 'done') return 'pending'
  if (vectorStore.isFileIndexed(file.file_path)) return 'success'
  return 'pending'
}

function getIndexStageIcon(file) {
  if (!file || file.state !== 'done') return '○'
  if (vectorStore.isFileIndexed(file.file_path)) return '✓'
  return '○'
}

function getIndexStageTime(file) {
  if (!file || file.state !== 'done') return '-'
  if (vectorStore.isFileIndexed(file.file_path)) return '14:34:00'
  return '-'
}

function isFileIndexed(file) {
  if (!file) return false
  return vectorStore.isFileIndexed(file.file_path)
}

function formatDate(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.drawer-file-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: var(--el-fill-color-lighter);
}

.drawer-file-icon.pdf {
  background: #fef2f2;
  color: #dc2626;
}

.drawer-file-icon.md {
  background: #f0f9ff;
  color: #0284c7;
}

.drawer-file-icon.audio {
  background: #f0fdf4;
  color: #16a34a;
}

.drawer-file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.drawer-file-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.drawer-file-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: flex;
  gap: 12px;
}

.drawer-content {
  padding: 0 24px 24px;
}

.error-section {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.error-icon {
  width: 24px;
  height: 24px;
  color: #ef4444;
}

.error-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.error-message {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.error-suggestion {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.error-actions {
  display: flex;
  gap: 10px;
}

.drawer-pipeline {
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 20px;
}

.drawer-pipeline-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 14px;
}

.drawer-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.drawer-step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.drawer-step-icon.pending {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-placeholder);
  border: 2px solid var(--el-border-color-lighter);
}

.drawer-step-icon.running {
  background: #4f46e5;
  color: white;
  animation: pulse 2s infinite;
}

.drawer-step-icon.success {
  background: #10b981;
  color: white;
}

.drawer-step-icon.failed {
  background: #ef4444;
  color: white;
}

.drawer-step-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.drawer-step-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.drawer-step-connector {
  width: 40px;
  height: 2px;
  background: var(--el-border-color-lighter);
  margin-bottom: 20px;
}

.drawer-step-connector.completed {
  background: #10b981;
}

.info-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.info-grid {
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  padding: 16px;
}

.info-row {
  display: flex;
  padding: 10px 0;
}

.info-row:not(:last-child) {
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.info-label {
  width: 90px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.info-value {
  flex: 1;
  font-size: 13px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.drawer-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 8px;
}

.chunk-table-container {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
}
</style>
```

**Step 2: 提交**
```bash
git add app/src/components/parse/ChunkDetailsDrawer.vue
git commit -m "feat: 添加ChunkDetailsDrawer增强版抽屉组件"
```

---

## 第二阶段：重构主页面

### Task 4: 重构 ParseManagement.vue 主页面

**Files:**
- Modify: `app/src/views/ParseManagement.vue`

**Step 1: 备份原文件（已在Task 0完成）**

**Step 2: 重写主页面**
```vue
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import { useRouter } from 'vue-router'
import FileManagementView from '@/components/parse/FileManagementView.vue'
import KanbanView from '@/components/parse/KanbanView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'

const router = useRouter()
const parseStore = useParseStore()
const vectorStore = useVectorStore()

const activeTab = ref('files')
const wsMineru = ref(null)
const wsAudio = ref(null)

function goBack() {
  router.push('/')
}

function refresh() {
  parseStore.fetchTasks()
  parseStore.fetchStats()
  vectorStore.loadStats()
  vectorStore.loadIndexedFiles()
}

// WebSocket 连接
function connectWebSocket() {
  // MinerU WebSocket
  try {
    wsMineru.value = new WebSocket('ws://localhost:8000/ws/tasks/mineru')
    wsMineru.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'task_update') {
        parseStore.fetchTasks()
        parseStore.fetchStats()
      }
    }
  } catch (e) {
    console.error('MinerU WebSocket连接失败:', e)
  }

  // Audio WebSocket
  try {
    wsAudio.value = new WebSocket('ws://localhost:8000/ws/tasks/audio')
    wsAudio.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'task_update') {
        parseStore.fetchTasks()
        parseStore.fetchStats()
      }
    }
  } catch (e) {
    console.error('Audio WebSocket连接失败:', e)
  }
}

function disconnectWebSocket() {
  if (wsMineru.value) {
    wsMineru.value.close()
  }
  if (wsAudio.value) {
    wsAudio.value.close()
  }
}

onMounted(async () => {
  await Promise.all([
    parseStore.fetchTasks(),
    parseStore.fetchStats(),
    vectorStore.loadStats(),
    vectorStore.loadIndexedFiles()
  ])
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<template>
  <div class="parse-management">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <h1 class="header-title">解析管理</h1>
      </div>
      <div class="header-right">
        <el-button @click="refresh">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/>
            </svg>
          </template>
          刷新
        </el-button>
      </div>
    </header>

    <!-- 顶部标签页 -->
    <div class="tabs-container">
      <el-tabs v-model="activeTab" class="parse-tabs">
        <el-tab-pane label="文件管理" name="files" />
        <el-tab-pane label="看板视图" name="kanban" />
        <el-tab-pane label="解析统计" name="stats" />
      </el-tabs>
    </div>

    <!-- 向量索引进度横幅 -->
    <div v-if="vectorStore.isIndexing" class="indexing-banner">
      <div class="indexing-content">
        <span class="indexing-text">
          正在索引: {{ vectorStore.currentIndexingFile }}
          ({{ vectorStore.indexingProgress }}/{{ vectorStore.indexingTotal }})
        </span>
        <el-progress
          :percentage="Math.round((vectorStore.indexingProgress / vectorStore.indexingTotal) * 100)"
          :stroke-width="8"
          style="width: 200px"
        />
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="main-content">
      <FileManagementView v-if="activeTab === 'files'" />
      <KanbanView v-if="activeTab === 'kanban'" />
      <ParseStatsView v-if="activeTab === 'stats'" />
    </div>
  </div>
</template>

<style scoped>
.parse-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.header {
  height: 56px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tabs-container {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 0 24px;
}

.parse-tabs {
  height: 100%;
}

.parse-tabs :deep(.el-tabs__content) {
  display: none;
}

.indexing-banner {
  background: #dbeafe;
  border-bottom: 1px solid #bfdbfe;
  padding: 12px 24px;
}

.indexing-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.indexing-text {
  font-size: 14px;
  font-weight: 500;
  color: #1e40af;
}

.main-content {
  flex: 1;
  overflow: hidden;
  padding: 20px 24px;
}
</style>
```

**Step 3: 提交**
```bash
git add app/src/views/ParseManagement.vue
git commit -m "feat: 重构ParseManagement主页面，添加顶部标签页"
```

---

### Task 5: 更新 ParseStatsView.vue（保留并增强）

**Files:**
- Modify: `app/src/components/parse/ParseStatsView.vue`

（此组件主要保留现有功能，可在后续优化，暂不做重大修改）

**Step 1: 确保组件能正常工作**
- 检查导入路径
- 验证与新主页面的兼容性

**Step 2: 提交（如有修改）**
```bash
git add app/src/components/parse/ParseStatsView.vue
git commit -m "chore: 确保ParseStatsView与新架构兼容"
```

---

## 第三阶段：集成与测试

### Task 6: 集成新抽屉组件到 FileManagementView 和 KanbanView

**Files:**
- Modify: `app/src/components/parse/FileManagementView.vue`
- Modify: `app/src/components/parse/KanbanView.vue`

**Step 1: 更新 FileManagementView 的抽屉**
```vue
// 在 FileManagementView.vue 中
import ChunkDetailsDrawer from './ChunkDetailsDrawer.vue'

// 替换 el-drawer 为 ChunkDetailsDrawer
<ChunkDetailsDrawer
  v-model:visible="drawerVisible"
  :file="selectedFile"
/>
```

**Step 2: 同样更新 KanbanView**

**Step 3: 提交**
```bash
git add app/src/components/parse/FileManagementView.vue app/src/components/parse/KanbanView.vue
git commit -m "feat: 集成ChunkDetailsDrawer到文件管理和看板视图"
```

---

### Task 7: 清理旧组件（可选，推荐在验证后执行）

**Files:**
- Delete: `app/src/components/Layout/ParseSidebar.vue`
- Delete: `app/src/components/parse/ParseQueueView.vue`
- Delete: `app/src/components/parse/ParseDocumentsView.vue`
- Delete: `app/src/components/parse/ParseDetailsDrawer.vue`
- Delete: `app/src/components/parse/AudioParseView.vue`（或保留作为占位）

**Step 1: 删除旧组件**
```bash
cd app/src
rm components/Layout/ParseSidebar.vue
rm components/parse/ParseQueueView.vue
rm components/parse/ParseDocumentsView.vue
rm components/parse/ParseDetailsDrawer.vue
```

**Step 2: 提交**
```bash
git add -u
git commit -m "chore: 移除旧的解析管理组件"
```

---

## 验证清单

- [ ] 主页面能正常加载
- [ ] 顶部标签页切换正常
- [ ] 文件管理表格显示正常
- [ ] 流水线步骤条显示正确
- [ ] 复选框批量选择功能正常
- [ ] Ctrl+A 全选功能正常
- [ ] 看板视图显示正常
- [ ] 统计视图显示正常
- [ ] 抽屉能正常打开和关闭
- [ ] WebSocket 实时更新正常
- [ ] 向量索引进度横幅正常显示

---

## 验收标准

### 功能验收
- [ ] 文件管理标签页能正确显示所有文件
- [ ] 表头显示"处理阶段 (上传→解析→索引→完成)"
- [ ] 复选框批量选择功能正常
- [ ] Ctrl+A 全选功能正常
- [ ] 选中行蓝色高亮
- [ ] 批量操作条显示选中数量
- [ ] 文件名悬停显示内容预览
- [ ] 筛选和搜索功能正常（正交筛选）
- [ ] 点击「详情」打开侧边抽屉
- [ ] 看板视图 4 列显示正常
- [ ] 统计标签页功能正常
- [ ] 所有现有功能正常工作

### UX 验收
- [ ] 顶部标签页切换流畅
- [ ] 步骤条清晰易理解
- [ ] 表头说明有帮助
- [ ] 表格视图信息清晰易读
- [ ] 侧边抽屉打开/关闭动画流畅
- [ ] 响应式布局在不同屏幕尺寸下正常

---

Plan complete and saved to `docs/plans/2026-03-07-parse-management-ux-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
