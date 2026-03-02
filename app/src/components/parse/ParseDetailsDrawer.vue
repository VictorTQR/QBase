<template>
  <el-drawer
    v-model="visibleLocal"
    title="解析详情"
    size="50%"
    :destroy-on-close="true"
  >
    <div v-if="fileData" class="parse-details">
      <div class="detail-section">
        <h4>文件信息</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="文件路径">{{ filePath }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ fileData.type || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="解析状态">
            <el-tag :type="getStatusType(fileData.status)">
              {{ getStatusLabel(fileData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="fileData.duration" label="解析耗时">
            {{ (fileData.duration / 1000).toFixed(1) }} 秒
          </el-descriptions-item>
          <el-descriptions-item v-if="fileData.size" label="文件大小">
            {{ formatSize(fileData.size) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="fileData.error" label="错误信息">
            <span class="error-text">{{ fileData.error }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="fileData.status === 'completed' && fileData.textPreview" class="detail-section">
        <h4>文本预览</h4>
        <div class="text-preview">
          {{ fileData.textPreview }}
        </div>
      </div>

      <div class="detail-actions">
        <el-button v-if="fileData.status === 'failed'" type="primary" @click="handleReparse">
          重新解析
        </el-button>
        <el-button v-else-if="fileData.status === 'completed'" type="primary" @click="handleReparse">
          重新解析
        </el-button>
        <el-button v-if="fileData.status === 'completed'" @click="handleExport">
          导出文本
        </el-button>
        <el-button type="danger" @click="handleDelete">
          删除记录
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useParseStore } from '@/stores/parse'

const props = defineProps({
  visible: { type: Boolean, default: false },
  filePath: { type: String, default: null },
})

const emit = defineEmits(['update:visible', 'close'])

const parseStore = useParseStore()
const visibleLocal = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const fileData = computed(() => {
  if (!props.filePath) return null
  return parseStore.parseIndex[props.filePath] || null
})

watch(() => props.visible, (val) => {
  if (!val) emit('close')
})

function getStatusType(status) {
  const map = {
    completed: 'success',
    parsing: 'primary',
    pending: 'warning',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    completed: '已完成',
    parsing: '解析中',
    pending: '待解析',
    failed: '失败',
  }
  return map[status] || status
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function handleReparse() {
  if (!props.filePath || !fileData.value) return
  try {
    await parseStore.startParse(props.filePath, fileData.value.fileType || fileData.value.type)
    ElMessage.success('开始重新解析')
  } catch (error) {
    ElMessage.error(`解析失败: ${error.message}`)
  }
}

function handleExport() {
  ElMessage.info('导出功能开发中')
}

async function handleDelete() {
  if (!props.filePath) return
  try {
    await ElMessageBox.confirm(
      '确定要删除这条解析记录吗？',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    parseStore.removeFile(props.filePath)
    visibleLocal.value = false
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.parse-details {
  padding: 0 20px 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.text-preview {
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-text {
  color: var(--el-color-danger);
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
