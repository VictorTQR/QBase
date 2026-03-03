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
        <div v-if="showActions" class="file-actions">
          <el-button
            v-if="!file.error"
            link
            type="primary"
            size="small"
            @click="$emit('parse', file)"
          >
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
