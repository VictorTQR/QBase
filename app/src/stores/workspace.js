import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useWorkspaceStore = defineStore('workspace', () => {
  const folders = ref([])
  const activeFileId = ref(null)
  const fileTree = ref({})

  function addFolder(folder) {
    const newFolder = {
      id: Date.now().toString(),
      name: folder.name,
      path: folder.path,
      type: 'folder',
    }
    folders.value.push(newFolder)
  }

  function removeFolder(folderId) {
    const index = folders.value.findIndex((f) => f.id === folderId)
    if (index !== -1) {
      folders.value.splice(index, 1)
    }
  }

  function refreshFileTree() {
    fileTree.value = {}
  }

  function selectFile(fileId) {
    activeFileId.value = fileId
  }

  return {
    folders,
    activeFileId,
    fileTree,
    addFolder,
    removeFolder,
    refreshFileTree,
    selectFile,
  }
})
