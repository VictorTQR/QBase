<script setup>
import { ref, computed, onMounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import { ElMessage, ElMessageBox } from 'element-plus'
import ChunkDetailsDrawer from './ChunkDetailsDrawer.vue'

const parseStore = useParseStore()
const vectorStore = useVectorStore()

const drawerVisible = ref(false)
const selectedFile = ref(null)

const isStarting = ref(false)
const isRetrying = ref(false)
const isDeleting = ref(false)

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

async function handleStartParse(file) {
  try {
    isStarting.value = true
    const response = await parseStore.batchParsePending()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '开始解析失败')
  } finally {
    isStarting.value = false
  }
}

async function handleRetry(file) {
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

async function handleDelete(file) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${file.file_name} 吗？`,
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
</script>

<template>
  <div class="kanban-view">
    <div class="kanban-container">
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
              <el-button type="primary" size="small" style="padding: 4px 10px; font-size: 12px" :loading="isStarting" @click.stop="handleStartParse(file)">
                开始
              </el-button>
            </div>
          </div>
        </div>
      </div>

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
                <el-button type="primary" size="small" style="padding: 4px 10px; font-size: 12px" :loading="isRetrying" @click.stop="handleRetry(file)">
                  重试
                </el-button>
                <el-button type="danger" size="small" style="padding: 4px 10px; font-size: 12px" :loading="isDeleting" @click.stop="handleDelete(file)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ChunkDetailsDrawer
      v-model:visible="drawerVisible"
      :file="selectedFile"
    />
  </div>
</template>

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
