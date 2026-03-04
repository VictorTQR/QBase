<template>
  <div class="parse-documents-view">
    <div class="view-header">
      <h2>已解析文档</h2>
      <div class="header-tools">
        <el-button
          type="primary"
          size="small"
          :disabled="doneTasksWithoutIndex.length === 0 || vectorStore.isIndexing"
          :loading="vectorStore.isIndexing"
          @click="handleBatchIndex"
        >
          批量索引向量
        </el-button>
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
          <div class="header-tags">
            <el-tag :type="parseStore.getStateType(task.state)" size="small">
              {{ parseStore.getStateLabel(task.state) }}
            </el-tag>
            <el-tag
              v-if="task.state === 'done'"
              :type="vectorStore.isFileIndexed(task.file_path) ? 'success' : 'info'"
              size="small"
            >
              {{ vectorStore.isFileIndexed(task.file_path) ? '已索引' : '未索引' }}
            </el-tag>
          </div>
        </div>
        <div class="card-body">
          <div class="document-title">{{ task.file_name }}</div>
          <div class="document-path" :title="task.file_path">
            {{ task.file_path || '未知路径' }}
          </div>
        </div>
        <div class="card-footer">
          <span class="file-hash" v-if="task.file_hash"
            >{{ task.file_hash.substring(0, 16) }}...</span
          >
          <span class="parser-type">{{ task.parser_type || 'mineru' }}</span>
          <el-button
            v-if="task.state === 'done'"
            type="primary"
            size="small"
            link
            :loading="vectorStore.isIndexing && vectorStore.currentIndexingFile === task.file_name"
            @click.stop="handleIndexDocument(task)"
          >
            索引向量
          </el-button>
        </div>
      </div>
    </div>

    <ParseDetailsDrawer v-model:visible="drawerVisible" :task="selectedTask" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CircleCheck, Loading, Clock, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import ParseDetailsDrawer from './ParseDetailsDrawer.vue'

const parseStore = useParseStore()
const vectorStore = useVectorStore()
const searchText = ref('')
const statusFilter = ref('')
const drawerVisible = ref(false)
const selectedTask = ref(null)

const filteredTasks = computed(() => {
  let result = [...parseStore.tasks]

  if (statusFilter.value) {
    result = result.filter((task) => task.state === statusFilter.value)
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(
      (task) =>
        (task.file_name && task.file_name.toLowerCase().includes(search)) ||
        (task.file_path && task.file_path.toLowerCase().includes(search)),
    )
  }

  return result
})

const doneTasksWithoutIndex = computed(() => {
  return parseStore.doneTasks.filter((task) => !vectorStore.isFileIndexed(task.file_path))
})

function handleSelectTask(task) {
  selectedTask.value = task
  drawerVisible.value = true
}

async function handleIndexDocument(task) {
  try {
    await vectorStore.indexDocument(
      task.file_path, 
      task.file_name, 
      null, 
      null,
      task.id
    )
    ElMessage.success(`已成功索引 ${task.file_name}`)
  } catch (err) {
    ElMessage.error(`索引失败: ${err.message}`)
  }
}

async function handleBatchIndex() {
  if (doneTasksWithoutIndex.value.length === 0) {
    ElMessage.warning('没有需要索引的文档')
    return
  }

  try {
    const result = await vectorStore.indexBatch(
      doneTasksWithoutIndex.value,
      null,
      null,
    )

    if (result.failed.length > 0) {
      ElMessage.warning(`成功索引 ${result.results.length} 个文档，失败 ${result.failed.length} 个`)
    } else {
      ElMessage.success(`成功索引 ${result.results.length} 个文档`)
    }
  } catch (err) {
    ElMessage.error(`批量索引失败: ${err.message}`)
  }
}

onMounted(async () => {
  try {
    await vectorStore.loadStats()
  } catch (err) {
    console.error('加载向量统计失败:', err)
  }
})
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
  align-items: center;
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

.header-tags {
  display: flex;
  gap: 8px;
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
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.card-footer .footer-left {
  display: flex;
  gap: 12px;
}

.card-footer span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
