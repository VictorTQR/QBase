<template>
  <div class="sidebar">
    <div class="workspace-title">工作区</div>
    <el-tree
      :data="treeData"
      :props="treeProps"
      node-key="id"
      default-expand-all
      @node-click="handleNodeClick"
      :highlight-current="true"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useDocumentStore } from '@/stores/document'

const workspaceStore = useWorkspaceStore()
const documentStore = useDocumentStore()

const treeProps = {
  children: 'children',
  label: 'name',
}

const treeData = ref([])

async function loadFolderTree(folder) {
  const result = await window.electronAPI.readDir(folder.path)
  if (result.success) {
    const children = [...result.folders, ...result.files]
    for (const child of result.folders) {
      const childResult = await window.electronAPI.readDir(child.path)
      if (childResult.success) {
        child.children = [...childResult.folders, ...childResult.files]
      }
    }
    return {
      ...folder,
      children,
    }
  }
  return folder
}

async function refreshTree() {
  const data = []
  for (const folder of workspaceStore.folders) {
    const treeNode = await loadFolderTree(folder)
    data.push(treeNode)
  }
  treeData.value = data
}

function handleNodeClick(data) {
  if (data.type === 'file') {
    workspaceStore.selectFile(data.id)
    documentStore.loadFile(data)
  }
}

watch(
  () => workspaceStore.folders,
  () => {
    refreshTree()
  },
  { deep: true },
)

onMounted(() => {
  refreshTree()
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

.workspace-title {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.sidebar :deep(.el-tree) {
  flex: 1;
  overflow-y: auto;
  border: none;
}
</style>
