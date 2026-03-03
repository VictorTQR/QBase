<template>
  <div class="parse-queue-view">
    <div class="view-header">
      <h2>队列管理</h2>
      <div class="header-actions">
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
import { ElMessage, ElMessageBox } from 'element-plus'

const parseStore = useParseStore()
const activeQueueTab = ref('running')
const isClearingCompleted = ref(false)
const isClearingAll = ref(false)

const pendingTasks = computed(() => parseStore.pendingTasks)
const runningTasks = computed(() => parseStore.runningTasks)
const failedTasks = computed(() => parseStore.failedTasks)
const doneTasks = computed(() => parseStore.doneTasks)

const handleClearCompleted = async () => {
  if (doneTasks.value.length === 0) {
    ElMessage.warning('没有已完成的任务可清除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要清除 ${doneTasks.value.length} 个已完成的任务吗？`,
      '确认清除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    isClearingCompleted.value = true
    const response = await parseStore.clearCompletedTasks()
    ElMessage.success(response.message)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '清除失败')
    }
  } finally {
    isClearingCompleted.value = false
  }
}

const handleClearAll = async () => {
  if (parseStore.tasks.length === 0) {
    ElMessage.warning('队列已经是空的')
    return
  }

  try {
    await ElMessageBox.confirm('确定要清空所有任务吗？此操作不可恢复！', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error',
    })

    isClearingAll.value = true
    const response = await parseStore.clearAllTasks()
    ElMessage.success(response.message)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '清空失败')
    }
  } finally {
    isClearingAll.value = false
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
