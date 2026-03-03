<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <span class="workspace-title">工作区</span>
      <div class="header-actions">
        <el-button :loading="isRefreshing" link type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="file-tree-container">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        lazy
        :load="loadNode"
        node-key="id"
        default-expand-all
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
        :highlight-current="true"
      />
    </div>

    <div class="sidebar-footer">
      <el-button type="primary" class="parse-management-btn" @click="goToParseManagement">
        <el-icon><Document /></el-icon>
        <span>解析管理</span>
      </el-button>
    </div>

    <teleport to="body">
      <div v-if="contextMenu.visible" class="context-menu" :style="contextMenu.style" @click.stop>
        <div
          v-if="contextMenu.nodeData?.type === 'file'"
          class="context-menu-item"
          @click="handleAddToParse"
        >
          添加到解析
        </div>
        <div
          v-if="
            contextMenu.nodeData?.type === 'folder' &&
            workspaceStore.folders.some((f) => f.id === contextMenu.nodeData?.id)
          "
          class="context-menu-item"
          @click="handleRemoveFolder"
        >
          移除文件夹
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Document } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useWorkspaceStore } from '@/stores/workspace'
import { useDocumentStore } from '@/stores/document'
import { useParseStore } from '@/stores/parse'

const router = useRouter()

function getFileType(fileName) {
  const ext = fileName.split('.').pop().toLowerCase()
  if (ext === 'md') return 'markdown'
  if (ext === 'pdf') return 'pdf'
  if (['mp3', 'wav', 'ogg', 'm4a', 'flac'].includes(ext)) return 'audio'
  if (['mp4', 'webm', 'mov', 'mkv'].includes(ext)) return 'video'
  return 'unknown'
}

const workspaceStore = useWorkspaceStore()
const documentStore = useDocumentStore()
const parseStore = useParseStore()

const treeProps = {
  children: 'children',
  label: 'name',
}

const treeData = ref([])
const treeRef = ref(null)
const isRefreshing = ref(false)

const contextMenu = ref({
  visible: false,
  style: { left: '0px', top: '0px' },
  nodeData: null,
})

async function loadNode(node, resolve) {
  if (node.level === 0) {
    return resolve([])
  }

  const nodeData = node.data
  if (nodeData.type === 'file') {
    return resolve([])
  }

  try {
    const result = await window.electronAPI.readDir(nodeData.path)
    if (result.success) {
      const children = [
        ...result.folders.map((f) => ({ ...f, leaf: false, loaded: false })),
        ...result.files.map((f) => ({ ...f, leaf: true })),
      ]
      return resolve(children)
    }
    return resolve([])
  } catch (error) {
    console.error('加载文件夹失败:', error)
    return resolve([])
  }
}

function initTreeData() {
  treeData.value = workspaceStore.folders.map((f) => ({
    ...f,
    leaf: false,
    loaded: false,
  }))
}

function handleContextMenu(event, data) {
  if (
    data.type === 'file' ||
    (data.type === 'folder' && workspaceStore.folders.some((f) => f.id === data.id))
  ) {
    event.preventDefault()
    event.stopPropagation()
    contextMenu.value = {
      visible: true,
      style: { left: `${event.clientX}px`, top: `${event.clientY}px` },
      nodeData: data,
    }
  }
}

function handleAddToParse() {
  contextMenu.value.visible = false
  const data = contextMenu.value.nodeData
  if (!data || data.type !== 'file') return

  const fileType = getFileType(data.name)
  if (fileType !== 'markdown' && fileType !== 'pdf' && fileType !== 'audio') {
    ElMessage.warning('仅支持 Markdown、PDF 和音频文件')
    return
  }

  parseStore.addFile(data.path, fileType)
  ElMessage.success('已添加到解析队列')
}

function handleClickOutside() {
  contextMenu.value.visible = false
}

async function handleRemoveFolder() {
  contextMenu.value.visible = false
  try {
    await ElMessageBox.confirm(
      `确定要移除文件夹「${contextMenu.value.nodeData.name}」吗？`,
      '移除文件夹',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    workspaceStore.removeFolder(contextMenu.value.nodeData.id)
  } catch {
    // 用户取消操作，忽略错误
  }
}

async function handleRefresh() {
  isRefreshing.value = true
  try {
    initTreeData()
  } finally {
    isRefreshing.value = false
  }
}

function handleNodeClick(data) {
  if (data.type === 'file') {
    workspaceStore.selectFile(data.id)
    documentStore.loadFile(data)
  }
}

function goToParseManagement() {
  router.push('/parse-management')
}

watch(
  () => workspaceStore.folders,
  () => {
    initTreeData()
  },
  { deep: true },
)

onMounted(() => {
  initTreeData()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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

.workspace-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.file-tree-container {
  flex: 1;
  overflow-y: auto;
}

.file-tree-container :deep(.el-tree) {
  border: none;
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

.context-menu {
  position: fixed;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 3000;
  min-width: 120px;
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.context-menu-item:hover {
  background: var(--el-fill-color-light);
}
</style>
