<template>
  <div class="parse-queue">
    <div class="queue-section">
      <div class="section-header">
        <span class="section-title">解析中 ({{ parsingFiles.length }})</span>
      </div>
      <div v-if="parsingFiles.length === 0" class="empty-state">暂无解析任务</div>
      <div v-else class="queue-list">
        <div v-for="item in parsingFiles" :key="item.filePath" class="queue-item">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span class="file-name">{{ getFileName(item.filePath) }}</span>
        </div>
      </div>
    </div>

    <div class="queue-section">
      <div class="section-header">
        <span class="section-title">待解析 ({{ pendingFiles.length }})</span>
      </div>
      <div v-if="pendingFiles.length === 0" class="empty-state">暂无待解析文件</div>
      <div v-else class="queue-list">
        <div v-for="item in pendingFiles" :key="item.filePath" class="queue-item">
          <el-icon><Clock /></el-icon>
          <span class="file-name">{{ getFileName(item.filePath) }}</span>
        </div>
      </div>
    </div>

    <div class="queue-section">
      <div class="section-header">
        <span class="section-title">失败 ({{ failedFiles.length }})</span>
      </div>
      <div v-if="failedFiles.length === 0" class="empty-state">暂无失败任务</div>
      <div v-else class="queue-list">
        <div v-for="item in failedFiles" :key="item.filePath" class="queue-item failed">
          <el-icon><CircleClose /></el-icon>
          <span class="file-name">{{ getFileName(item.filePath) }}</span>
          <el-tooltip :content="item.error" placement="top">
            <el-icon class="error-icon"><WarningFilled /></el-icon>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Clock, Loading, CircleClose, WarningFilled } from '@element-plus/icons-vue'

defineProps({
  pendingFiles: { type: Array, default: () => [] },
  parsingFiles: { type: Array, default: () => [] },
  failedFiles: { type: Array, default: () => [] },
})

function getFileName(filePath) {
  return filePath.split(/[\\/]/).pop() || filePath
}
</script>

<style scoped>
.parse-queue {
  padding: 12px;
  border-right: 1px solid var(--el-border-color-lighter);
  overflow-y: auto;
  flex: 1;
}

.queue-section {
  margin-bottom: 16px;
}

.section-header {
  margin-bottom: 8px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.empty-state {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  padding: 8px 0;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 4px;
  background: var(--el-fill-color-lighter);
  font-size: 12px;
}

.queue-item.failed {
  background: rgba(245, 108, 108, 0.1);
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

.error-icon {
  color: var(--el-color-warning);
  cursor: pointer;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
