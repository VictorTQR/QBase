import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { workspaceManager } from '@/utils/workspaceManager'

let initialized = false

export const useWorkspaceStore = defineStore(
  'workspace',
  () => {
    const currentWorkspace = ref(null)
    const activeFileId = ref(null)
    const needsRefresh = ref(false)

    const isWorkspaceSelected = computed(() => currentWorkspace.value !== null)
    const workspaceName = computed(() => {
      if (!currentWorkspace.value || typeof currentWorkspace.value !== 'string') return ''
      return currentWorkspace.value.split(/[/\\]/).pop()
    })

    async function ensureInitialized() {
      if (!initialized) {
        await workspaceManager.init()
        initialized = true
      }
    }

    async function setCurrentWorkspace(workspacePath) {
      await ensureInitialized()
      currentWorkspace.value = workspacePath
      await workspaceManager.setLastWorkspace(workspacePath)
    }

    function clearCurrentWorkspace() {
      currentWorkspace.value = null
    }

    function fixCorruptedWorkspace() {
      if (currentWorkspace.value !== null && typeof currentWorkspace.value !== 'string') {
        console.warn('检测到损坏的工作区数据，已重置:', currentWorkspace.value)
        currentWorkspace.value = null
      }
    }

    function refreshFileTree() {
      needsRefresh.value = !needsRefresh.value
    }

    function selectFile(fileId) {
      activeFileId.value = fileId
    }

    async function initializeFromLastWorkspace() {
      await ensureInitialized()
      const lastWorkspace = await workspaceManager.getLastWorkspace()
      if (lastWorkspace) {
        currentWorkspace.value = lastWorkspace
      }
    }

    return {
      currentWorkspace,
      activeFileId,
      needsRefresh,
      isWorkspaceSelected,
      workspaceName,
      setCurrentWorkspace,
      clearCurrentWorkspace,
      refreshFileTree,
      selectFile,
      initializeFromLastWorkspace,
      fixCorruptedWorkspace,
    }
  },
  {
    persist: {
      key: 'qbase-workspace',
      paths: ['currentWorkspace'],
    },
  },
)
