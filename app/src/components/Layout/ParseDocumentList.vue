<template>
  <div class="parse-document-list">
    <div class="list-header">
      <span class="header-title">文档列表</span>
    </div>
    <div class="list-content">
      <el-empty v-if="Object.keys(parseIndex).length === 0" description="暂无解析记录" />
      <div v-else class="document-items">
        <div
          v-for="(data, filePath) in parseIndex"
          :key="filePath"
          class="document-item"
          :class="{ selected: selectedFile === filePath }"
          @click="handleSelect(filePath)"
        >
          <el-icon class="status-icon" :class="data.status">
            <CircleCheck v-if="data.status === 'completed'" />
            <Loading v-else-if="data.status === 'parsing'" class="spinning" />
            <Clock v-else-if="data.status === 'pending'" />
            <CircleClose v-else />
          </el-icon>
          <div class="file-info">
            <div class="file-name">{{ getFileName(filePath) }}</div>
            <div class="file-meta">
              <span class="file-type">{{ data.type || '未知' }}</span>
              <span v-if="data.duration" class="file-duration"
                >{{ (data.duration / 1000).toFixed(1) }}s</span
              >
              <span v-if="data.size" class="file-size">{{ formatSize(data.size) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CircleCheck, Loading, Clock, CircleClose } from '@element-plus/icons-vue'

defineProps({
  parseIndex: { type: Object, default: () => ({}) },
  selectedFile: { type: String, default: null },
})

const emit = defineEmits(['select'])

function getFileName(filePath) {
  return filePath.split(/[\\/]/).pop() || filePath
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleSelect(filePath) {
  emit('select', filePath)
}
</script>

<style scoped>
.parse-document-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.list-header {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.document-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.document-item:hover {
  background: var(--el-fill-color-lighter);
}

.document-item.selected {
  background: var(--el-fill-color-light);
}

.status-icon {
  font-size: 16px;
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

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 8px;
  margin-top: 2px;
}

.file-type,
.file-duration,
.file-size {
  font-size: 11px;
  color: var(--el-text-color-secondary);
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
