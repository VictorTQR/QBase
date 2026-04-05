<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="workspace-info">
        <span class="workspace-icon">📁</span>
        <span class="workspace-name">{{ workspaceStore.workspaceName }}</span>
      </div>
      <div class="header-actions">
        <el-button :loading="fileManagementStore.isScanning" link type="primary" @click="handleScan">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div v-if="fileManagementStore.scanStats" class="scan-stats">
      <span class="stat-item">新增: {{ fileManagementStore.scanStats.new_files }}</span>
      <span class="stat-item">修改: {{ fileManagementStore.scanStats.modified_files }}</span>
    </div>

    <div class="file-tree-container">
      <div v-if="fileManagementStore.files.length > 0" class="file-list">
        <div
          v-for="file in fileManagementStore.files"
          :key="file.hash"
          class="file-item"
          :class="{ active: fileManagementStore.selectedFile?.hash === file.hash }"
          @click="handleFileClick(file)"
        >
          <span class="file-icon">{{ getFileIcon(file.file_type) }}</span>
          <span class="file-name">{{ file.rel_path.split('/').pop() }}</span>
          <span class="file-status" :class="file.status">{{ getStatusText(file.status) }}</span>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-empty description="暂无文件，点击刷新按钮扫描" />
      </div>
    </div>

    <div class="sidebar-footer">
      <el-button type="primary" class="parse-management-btn" @click="goToParseManagement">
        <el-icon><Document /></el-icon>
        <span>解析管理</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Document } from '@element-plus/icons-vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useDocumentStore } from '@/stores/document'
import { useFileManagementStore } from '@/stores/fileManagement'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const documentStore = useDocumentStore()
const fileManagementStore = useFileManagementStore()

function getFileIcon(fileType) {
  const icons = {
    'markdown': '📝',
    'pdf': '📄',
    'audio': '🎵',
    'video': '🎬',
  }
  return icons[fileType] || '📄'
}

function getStatusText(status) {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'ready': '就绪',
    'error': '错误',
    'missing': '缺失',
    'orphan': '孤立',
  }
  return texts[status] || status
}

async function handleFileClick(file) {
  fileManagementStore.selectFile(file)
  
  const workspacePath = workspaceStore.currentWorkspace
  if (workspacePath) {
    const fullPath = `${workspacePath}/${file.rel_path}`
    const fileData = {
      id: file.hash,
      name: file.rel_path.split('/').pop(),
      path: fullPath,
      type: 'file',
      fileType: file.file_type,
    }
    documentStore.loadFile(fileData)
  }
}

async function handleScan() {
  const workspacePath = workspaceStore.currentWorkspace
  if (workspacePath) {
    await fileManagementStore.initializeAndScanWorkspace(workspacePath)
  }
}

function goToParseManagement() {
  router.push('/parse-management')
}

onMounted(() => {
  const workspacePath = workspaceStore.currentWorkspace
  if (workspacePath) {
    fileManagementStore.initializeAndScanWorkspace(workspacePath)
  }
})
</script>

<style scoped>
.sidebar {
  width: 25%;
  min-width: 200px;
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.workspace-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.workspace-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.workspace-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.scan-stats {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  gap: 16px;
}

.stat-item {
  display: inline-flex;
  align-items: center;
}

.file-tree-container {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.file-list {
  display: flex;
  flex-direction: column;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  gap: 8px;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: var(--el-fill-color-light);
}

.file-item.active {
  background-color: var(--el-fill-color);
}

.file-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.file-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.file-status.pending {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.file-status.processing {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.file-status.ready {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.file-status.error {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.file-status.missing {
  background-color: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.empty-state {
  padding: 32px 16px;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.parse-management-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>
