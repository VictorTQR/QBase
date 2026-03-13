<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import { ElMessage, ElCheckbox, ElMessageBox } from 'element-plus'
import ChunkDetailsDrawer from './ChunkDetailsDrawer.vue'

const parseStore = useParseStore()
const vectorStore = useVectorStore()

const selectedFiles = ref(new Set())
const selectAll = ref(false)
const fileTypeFilter = ref('')
const statusFilter = ref('')
const searchText = ref('')

const drawerVisible = ref(false)
const selectedFile = ref(null)

const isBatchParsing = ref(false)
const isBatchIndexing = ref(false)
const isDeleting = ref(false)

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
  
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    files = files.filter(f => 
      f.file_name.toLowerCase().includes(search) ||
      f.file_path?.toLowerCase().includes(search)
    )
  }
  
  if (fileTypeFilter.value) {
    files = files.filter(f => {
      if (fileTypeFilter.value === 'document') {
        return f.parser_type === 'mineru' || f.file_name?.endsWith('.md')
      } else if (fileTypeFilter.value === 'audio') {
        return f.parser_type === 'audio'
      }
      return true
    })
  }
  
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

const pendingTasks = computed(() => parseStore.pendingTasks)
const doneTasksWithoutIndex = computed(() => {
  return parseStore.doneTasks.filter((task) => !vectorStore.isFileIndexed(task.file_path))
})
const selectedFilesArray = computed(() => {
  return filteredFiles.value.filter(f => selectedFiles.value.has(f.id))
})

function toggleSelectAll() {
  if (selectAll.value) {
    selectedFiles.value = new Set(filteredFiles.value.map(f => f.id))
  } else {
    selectedFiles.value = new Set()
  }
}

function toggleFileSelection(fileId) {
  const newSet = new Set(selectedFiles.value)
  if (newSet.has(fileId)) {
    newSet.delete(fileId)
  } else {
    newSet.add(fileId)
  }
  selectedFiles.value = newSet // 触发响应式更新
  selectAll.value = newSet.size === filteredFiles.value.length
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})

function handleKeyDown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
    e.preventDefault()
    selectAll.value = true
    toggleSelectAll()
  }
}

function openDrawer(file) {
  selectedFile.value = file
  drawerVisible.value = true
}

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
  return '-'
}

async function handleBatchParse() {
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

async function handleBatchIndex() {
  const filesToIndex = selectedFilesArray.value.length > 0 
    ? selectedFilesArray.value.filter(f => f.state === 'done' && !f.vectorIndexed)
    : doneTasksWithoutIndex.value

  if (filesToIndex.length === 0) {
    ElMessage.warning('没有需要索引的文档')
    return
  }

  try {
    isBatchIndexing.value = true
    const result = await vectorStore.indexBatch(
      filesToIndex,
      async (taskId) => {
        const content = await parseStore.getTaskResult(taskId)
        return content?.markdown_content || null
      },
      null,
    )

    if (result.failed.length > 0) {
      ElMessage.warning(`成功索引 ${result.results.length} 个文档，失败 ${result.failed.length} 个`)
    } else {
      ElMessage.success(`成功索引 ${result.results.length} 个文档`)
    }
  } catch (err) {
    ElMessage.error(`批量索引失败: ${err.message}`)
  } finally {
    isBatchIndexing.value = false
  }
}

async function handleDeleteSelected() {
  if (selectedFiles.value.size === 0) {
    ElMessage.warning('请先选择要删除的文件')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFiles.value.size} 个文件吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    isDeleting.value = true
    ElMessage.info('删除功能待后端 API 支持')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  } finally {
    isDeleting.value = false
  }
}

async function handleRetry(file) {
  try {
    const response = await parseStore.retryFailedTasks()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '重试失败')
  }
}

async function handleIndex(file) {
  try {
    await vectorStore.indexDocument(
      file.file_path,
      file.file_name,
      null,
      null,
      file.id
    )
    ElMessage.success(`已成功索引 ${file.file_name}`)
  } catch (err) {
    ElMessage.error(`索引失败: ${err.message}`)
  }
}
</script>

<template>
  <div class="file-management-view">
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

    <div v-if="selectedFiles.size > 0" class="batch-action-bar">
      <div class="batch-info">
        <span class="batch-count">{{ selectedFiles.size }}</span>
        <span>个文件已选中</span>
      </div>
      <div class="batch-buttons">
        <el-button type="primary" size="small" :loading="isBatchParsing" :disabled="pendingTasks.length === 0" @click="handleBatchParse">批量解析</el-button>
        <el-button size="small" :loading="isBatchIndexing" :disabled="doneTasksWithoutIndex.length === 0" @click="handleBatchIndex">批量索引</el-button>
        <el-button type="danger" size="small" :loading="isDeleting" :disabled="selectedFiles.size === 0" @click="handleDeleteSelected">删除</el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="filteredFiles" style="width: 100%; min-width: 900px;" table-layout="auto">
        <el-table-column min-width="8%">
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

        <el-table-column label="文件名" min-width="32%">
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

        <el-table-column label="处理阶段 (上传→解析→索引→完成)" min-width="30%">
          <template #default="{ row }">
            <div class="pipeline-stepper">
              <div class="step">
                <div class="step-icon success">✓</div>
              </div>
              <div class="step-connector" :class="{ completed: row.state !== 'pending' }"></div>
              
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

        <el-table-column label="文件信息" min-width="18%">
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

        <el-table-column label="操作" min-width="12%">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="openDrawer(row)">
                详情
              </el-button>
              <el-button v-if="row.state === 'failed'" size="small" @click="handleRetry(row)">
                重试
              </el-button>
              <el-button
                v-if="row.state === 'done' && !row.vectorIndexed"
                type="primary"
                size="small"
                :loading="vectorStore.isIndexing && vectorStore.currentIndexingFile === row.file_name"
                @click="handleIndex(row)"
              >
                索引
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <ChunkDetailsDrawer
      v-model:visible="drawerVisible"
      :file="selectedFile"
    />
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

.table-container :deep(.el-table) {
  width: 100%;
}

.table-container :deep(.el-table__header-wrapper th) {
  background: var(--el-fill-color-light) !important;
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
