import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

export const useWorkspaceStore = defineStore(
  'workspace',
  () => {
    const folders = ref([])
    const activeFileId = ref(null)
    const needsRefresh = ref(false)

    function addFolder(folder) {
      const exists = folders.value.some((f) => f.path === folder.path)
      if (exists) {
        ElMessage.warning('该文件夹已在工作区中')
        return
      }
      const newFolder = {
        id: Date.now().toString(),
        name: folder.name,
        path: folder.path,
        type: 'folder',
      }
      folders.value.push(newFolder)
      ElMessage.success('文件夹添加成功')
    }

    function removeFolder(folderId) {
      const index = folders.value.findIndex((f) => f.id === folderId)
      if (index !== -1) {
        folders.value.splice(index, 1)
        ElMessage.success('文件夹已移除')
      }
    }

    function refreshFileTree() {
      needsRefresh.value = !needsRefresh.value
    }

    function selectFile(fileId) {
      activeFileId.value = fileId
    }

    return {
      folders,
      activeFileId,
      needsRefresh,
      addFolder,
      removeFolder,
      refreshFileTree,
      selectFile,
    }
  },
  {
    persist: {
      key: 'qbase-workspace',
      paths: ['folders'],
    },
  },
)
