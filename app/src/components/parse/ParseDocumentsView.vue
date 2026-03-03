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

    <ParseDetailsDrawer v-model:visible="drawerVisible" :task="selectedTask" />
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
const drawerVisible = ref(false)
const selectedTask = ref(null)

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
  selectedTask.value = task
  drawerVisible.value = true
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
