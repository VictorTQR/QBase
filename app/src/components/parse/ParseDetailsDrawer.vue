<template>
  <el-drawer :model-value="visible" title="解析详情" size="50%" @close="handleClose">
    <div v-if="task" class="parse-details-drawer">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="文件名">
          {{ task.file_name }}
        </el-descriptions-item>
        <el-descriptions-item label="文件路径">
          <el-input v-model="task.file_path" readonly :border="false" />
        </el-descriptions-item>
        <el-descriptions-item label="任务ID">
          {{ task.id }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStateType(task.state)">
            {{ getStateLabel(task.state) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="解析器">
          {{ task.parser_type || 'mineru' }}
        </el-descriptions-item>
        <el-descriptions-item label="文件哈希">
          {{ task.file_hash || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ task.created_at ? formatDate(task.created_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ task.updated_at ? formatDate(task.updated_at) : '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <div v-if="task.error_msg" class="error-section">
        <h4>错误信息</h4>
        <el-alert type="error" :closable="false">
          {{ task.error_msg }}
        </el-alert>
      </div>

      <div v-if="task.markdown_content" class="content-preview">
        <h4>内容预览</h4>
        <div class="preview-box">
          {{ task.markdown_content.substring(0, 500) }}
          {{ task.markdown_content.length > 500 ? '...' : '' }}
        </div>
      </div>
    </div>
    <div v-else class="parse-details-drawer">
      <el-empty description="请选择一个任务" />
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  task: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'close'])

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

function getStateType(state) {
  const map = {
    done: 'success',
    running: 'primary',
    pending: 'warning',
    failed: 'danger'
  }
  return map[state] || 'info'
}

function getStateLabel(state) {
  const map = {
    done: '已完成',
    running: '解析中',
    pending: '待解析',
    failed: '失败'
  }
  return map[state] || state
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.parse-details-drawer {
  padding: 16px;
}

.error-section h4,
.content-preview h4 {
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.preview-box {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
