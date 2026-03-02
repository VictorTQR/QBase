<template>
  <div class="parse-queue-view">
    <div class="view-header">
      <h2>队列管理</h2>
      <div class="header-actions">
        <el-button size="small" @click="handleClearCompleted">清除已完成</el-button>
        <el-button size="small" type="danger" @click="handleClearAll" :disabled="totalCount === 0">
          清空队列
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeQueueTab" class="queue-tabs">
      <el-tab-pane label="解析中" name="parsing">
        <FileList :files="parsingFiles" :show-progress="true" />
      </el-tab-pane>
      <el-tab-pane label="待解析" name="pending">
        <FileList :files="pendingFiles" :show-actions="true" @parse="handleParseFile" @remove="handleRemoveFile" />
      </el-tab-pane>
      <el-tab-pane label="失败" name="failed">
        <FileList :files="failedFiles" :show-error="true" :show-actions="true" @retry="handleRetryFile" @remove="handleRemoveFile" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useParseStore } from '@/stores/parse'
import FileList from './FileList.vue'

const parseStore = useParseStore()
const activeQueueTab = ref('parsing')

const pendingFiles = computed(() => parseStore.pendingFiles)
const parsingFiles = computed(() => parseStore.parsingFiles)
const failedFiles = computed(() => parseStore.failedFiles)

const totalCount = computed(() => 
  pendingFiles.value.length + parsingFiles.value.length + failedFiles.value.length
)

async function handleParseFile(file) {
  try {
    await parseStore.startParse(file.filePath, file.fileType)
    ElMessage.success('开始解析')
  } catch (error) {
    ElMessage.error(`解析失败: ${error.message}`)
  }
}

async function handleRetryFile(file) {
  try {
    await parseStore.startParse(file.filePath, file.fileType)
    ElMessage.success('开始重试')
  } catch (error) {
    ElMessage.error(`重试失败: ${error.message}`)
  }
}

function handleRemoveFile(file) {
  parseStore.removeFile(file.filePath)
  ElMessage.success('已移除')
}

function handleClearCompleted() {
  ElMessage.info('清除已完成功能开发中')
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm(
      '确定要清空整个队列吗？此操作不可恢复。',
      '清空队列',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    ElMessage.info('清空队列功能开发中')
  } catch {
    // 用户取消
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
</style>
