import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { workspaceBackendApi } from '@/api/workspaceBackend'
import { fileBackendApi } from '@/api/fileBackend'
import { useWorkspaceStore } from './workspace'

export const useFileManagementStore = defineStore('fileManagement', () => {
  const workspaceStore = useWorkspaceStore()

  const files = ref([])
  const totalFiles = ref(0)
  const isLoading = ref(false)
  const isScanning = ref(false)
  const scanStats = ref(null)
  const selectedFile = ref(null)

  const currentWorkspacePath = computed(() => {
    return workspaceStore.currentWorkspace
  })

  const pendingFiles = computed(() => files.value.filter((f) => f.status === 'pending'))

  const readyFiles = computed(() => files.value.filter((f) => f.status === 'ready'))

  const missingFiles = computed(() => files.value.filter((f) => f.status === 'missing'))

  async function initializeAndScan() {
    const workspacePath = currentWorkspacePath.value
    if (!workspacePath) {
      ElMessage.warning('请先添加工作区文件夹')
      return
    }
    await initializeAndScanWorkspace(workspacePath)
  }

  async function initializeAndScanWorkspace(workspacePath) {
    try {
      if (!workspacePath || typeof workspacePath !== 'string') {
        console.warn('无效的工作区路径:', workspacePath)
        return
      }

      isLoading.value = true

      // 检查并初始化工作区
      const initCheck = await workspaceBackendApi.checkInitialized(workspacePath)
      if (!initCheck.initialized) {
        await workspaceBackendApi.initializeWorkspace(workspacePath)
        ElMessage.success('工作区初始化成功')
      }

      // 扫描工作区
      await scanWorkspace(workspacePath)
    } catch (error) {
      console.error('初始化工作区失败:', error)
      ElMessage.error(`初始化失败: ${error.message}`)
    } finally {
      isLoading.value = false
    }
  }

  async function scanWorkspace(workspacePath, forceHash = false) {
    try {
      isScanning.value = true
      scanStats.value = null

      const result = await workspaceBackendApi.scanWorkspace(workspacePath, forceHash)
      scanStats.value = result.stats

      ElMessage.success(
        `扫描完成: 新增 ${result.stats.new_files} 个，修改 ${result.stats.modified_files} 个`,
      )

      // 刷新文件列表
      await loadFiles(workspacePath)
    } catch (error) {
      console.error('扫描工作区失败:', error)
      ElMessage.error(`扫描失败: ${error.message}`)
    } finally {
      isScanning.value = false
    }
  }

  async function loadFiles(workspacePath, options = {}) {
    try {
      isLoading.value = true

      const result = await fileBackendApi.listFiles(workspacePath, options)
      files.value = result.files
      totalFiles.value = result.total
    } catch (error) {
      console.error('加载文件列表失败:', error)
      ElMessage.error(`加载失败: ${error.message}`)
    } finally {
      isLoading.value = false
    }
  }

  async function loadFileDetail(fileHash, workspacePath) {
    try {
      const result = await fileBackendApi.getFile(fileHash, workspacePath)
      selectedFile.value = result.file
      return result.file
    } catch (error) {
      console.error('加载文件详情失败:', error)
      ElMessage.error(`加载失败: ${error.message}`)
    }
  }

  function selectFile(file) {
    selectedFile.value = file
  }

  function clearSelection() {
    selectedFile.value = null
  }

  return {
    files,
    totalFiles,
    isLoading,
    isScanning,
    scanStats,
    selectedFile,
    currentWorkspacePath,
    pendingFiles,
    readyFiles,
    missingFiles,
    initializeAndScan,
    initializeAndScanWorkspace,
    scanWorkspace,
    loadFiles,
    loadFileDetail,
    selectFile,
    clearSelection,
  }
})
