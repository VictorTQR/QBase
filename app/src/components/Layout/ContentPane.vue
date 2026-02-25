<template>
  <div class="content-pane">
    <div v-if="documentStore.currentFile" class="file-header">
      <el-icon><Document /></el-icon>
      <span class="file-path">{{ documentStore.currentFile.path }}</span>
    </div>
    <div v-else class="empty-state">
      <el-empty description="请选择一个文件" />
    </div>
    <div v-if="documentStore.isLoading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else-if="documentStore.error" class="error">
      <el-icon><Warning /></el-icon>
      <span>{{ documentStore.error }}</span>
    </div>
    <DocumentViewer v-else-if="documentStore.currentFile" />
  </div>
</template>

<script setup>
import { Document, Loading, Warning } from '@element-plus/icons-vue'
import { useDocumentStore } from '@/stores/document'
import DocumentViewer from '@/components/DocumentViewer.vue'

const documentStore = useDocumentStore()
</script>

<style scoped>
.content-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--el-bg-color-page);
}

.file-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-bg-color);
}

.file-path {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.empty-state,
.loading,
.error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
}
</style>
