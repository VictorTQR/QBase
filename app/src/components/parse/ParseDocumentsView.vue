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
          <el-option label="已完成" value="completed" />
          <el-option label="解析中" value="parsing" />
          <el-option label="待解析" value="pending" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
    </div>

    <div v-if="Object.keys(filteredDocuments).length === 0" class="empty-state">
      <el-empty description="暂无解析文档" />
    </div>
    <div v-else class="document-grid">
      <div
        v-for="(data, filePath) in filteredDocuments"
        :key="filePath"
        class="document-card"
        @click="handleSelectDocument(filePath)"
      >
        <div class="card-header">
          <el-icon class="status-icon" :class="data.status">
            <CircleCheck v-if="data.status === 'completed'" />
            <Loading v-else-if="data.status === 'parsing'" class="spinning" />
            <Clock v-else-if="data.status === 'pending'" />
            <CircleClose v-else />
          </el-icon>
          <el-tag :type="parseStore.getStatusType(data.status)" size="small">
            {{ parseStore.getStatusLabel(data.status) }}
          </el-tag>
        </div>
        <div class="card-body">
          <div class="document-title">{{ getFileName(filePath) }}</div>
          <div class="document-path" :title="filePath">{{ filePath }}</div>
        </div>
        <div class="card-footer">
          <span class="file-type">{{ data.type || '未知' }}</span>
          <span v-if="data.duration" class="file-duration">
            {{ (data.duration / 1000).toFixed(1) }}s
          </span>
          <span v-if="data.size" class="file-size">{{ formatSize(data.size) }}</span>
        </div>
      </div>
    </div>

    <ParseDetailsDrawer
      v-model:visible="detailsVisible"
      :file-path="selectedFilePath"
      @close="detailsVisible = false"
    />
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
const detailsVisible = ref(false)
const selectedFilePath = ref(null)

const filteredDocuments = computed(() => {
  const index = parseStore.parseIndex
  let result = { ...index }

  if (statusFilter.value) {
    result = Object.fromEntries(
      Object.entries(result).filter(([, data]) => data.status === statusFilter.value)
    )
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = Object.fromEntries(
      Object.entries(result).filter(([filePath]) =>
        filePath.toLowerCase().includes(search)
      )
    )
  }

  return result
})

function getFileName(filePath) {
  return filePath.split(/[\\/]/).pop() || filePath
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleSelectDocument(filePath) {
  selectedFilePath.value = filePath
  detailsVisible.value = true
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
