<template>
  <div class="parse-details" v-if="fileData">
    <div class="details-header">
      <span class="details-title">解析详情</span>
      <el-button link size="small" @click="$emit('close')">
        <el-icon><Close /></el-icon>
      </el-button>
    </div>

    <div class="details-content">
      <div class="detail-row">
        <span class="detail-label">文件</span>
        <span class="detail-value">{{ getFileName(filePath) }}</span>
      </div>

      <div class="detail-row">
        <span class="detail-label">状态</span>
        <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
      </div>

      <div class="detail-row" v-if="fileData.type">
        <span class="detail-label">类型</span>
        <span class="detail-value">{{ fileData.type }}</span>
      </div>

      <div class="detail-row" v-if="fileData.duration">
        <span class="detail-label">耗时</span>
        <span class="detail-value">{{ (fileData.duration / 1000).toFixed(2) }}s</span>
      </div>

      <div class="detail-row" v-if="fileData.size">
        <span class="detail-label">大小</span>
        <span class="detail-value">{{ formatSize(fileData.size) }}</span>
      </div>

      <div class="detail-row" v-if="fileData.error">
        <span class="detail-label">错误</span>
        <span class="detail-value error">{{ fileData.error }}</span>
      </div>
    </div>

    <div class="details-actions">
      <el-button size="small" @click="$emit('reparse')">重新解析</el-button>
      <el-button size="small" type="danger" @click="$emit('delete')">删除记录</el-button>
    </div>
  </div>
  <div class="parse-details empty" v-else>
    <div class="empty-tip">选择文档查看详情</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Close } from '@element-plus/icons-vue'

const props = defineProps({
  filePath: { type: String, default: null },
  fileData: { type: Object, default: null }
})

defineEmits(['close', 'reparse', 'delete'])

const statusText = computed(() => {
  const statusMap = {
    pending: '待解析',
    parsing: '解析中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[props.fileData?.status] || '未知'
})

const statusType = computed(() => {
  const typeMap = {
    pending: 'warning',
    parsing: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[props.fileData?.status] || ''
})

function getFileName(path) {
  return path?.split(/[\\/]/).pop() || path
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.parse-details {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.parse-details.empty {
  justify-content: center;
  align-items: center;
  min-height: 120px;
}

.empty-tip {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.details-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.detail-label {
  width: 60px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  font-size: 12px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-value.error {
  color: var(--el-color-danger);
}

.details-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
