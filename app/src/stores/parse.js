import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { ParseBackendApi } from '@/api/parseBackend'
import { useAudioStore } from '@/stores/audio'
import { useParseConfigStore } from '@/stores/parseConfig'

export const useParseStore = defineStore('parse', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const stats = ref({
    total: 0,
    pending: 0,
    running: 0,
    done: 0,
    failed: 0,
  })
  const isLoading = ref(false)
  const error = ref(null)

  const tasksByState = computed(() => {
    const groups = {
      pending: [],
      running: [],
      done: [],
      failed: [],
    }
    tasks.value.forEach((task) => {
      if (groups[task.state]) {
        groups[task.state].push(task)
      }
    })
    return groups
  })

  const pendingTasks = computed(() => tasksByState.value.pending)
  const runningTasks = computed(() => tasksByState.value.running)
  const doneTasks = computed(() => tasksByState.value.done)
  const failedTasks = computed(() => tasksByState.value.failed)

  async function fetchTasks(limit = 100, offset = 0) {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.listTasks(limit, offset)
      tasks.value = response.tasks || []
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTask(taskId) {
    try {
      const task = await ParseBackendApi.getTask(taskId)
      const index = tasks.value.findIndex((t) => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = task
      }
      currentTask.value = task
      return task
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function fetchStats() {
    try {
      const statsData = await ParseBackendApi.getStats()
      if (statsData) {
        stats.value = statsData
      }
      return stats.value
    } catch (err) {
      console.error('获取统计失败:', err)
      error.value = err.message || '获取统计数据失败'
    }
  }

  async function checkDuplicate(params) {
    try {
      return await ParseBackendApi.checkDuplicate(params)
    } catch (err) {
      console.error('去重检查失败:', err)
      return { is_duplicate: false }
    }
  }

  async function parseLocalFile(filePath) {
    isLoading.value = true
    error.value = null
    try {
      const task = await ParseBackendApi.parseLocalFile(filePath)
      if (!task.is_duplicate) {
        await fetchTasks()
        await fetchStats()
      }
      return task
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getTaskResult(taskId) {
    try {
      return await ParseBackendApi.getTaskResult(taskId)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function pollTaskUntilDone(taskId, interval = 3000, maxAttempts = 600) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const task = await fetchTask(taskId)
      if (task.state === 'done') {
        return { success: true, task }
      } else if (task.state === 'failed') {
        return { success: false, error: task.error_msg, task }
      }
      await new Promise((resolve) => setTimeout(resolve, interval))
    }
    return { success: false, error: '超时' }
  }

  function getStateType(state) {
    const map = {
      done: 'success',
      running: 'primary',
      pending: 'warning',
      failed: 'danger',
    }
    return map[state] || 'info'
  }

  function getStateLabel(state) {
    const map = {
      done: '已完成',
      running: '解析中',
      pending: '待解析',
      failed: '失败',
    }
    return map[state] || state
  }

  async function clearCompletedTasks() {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.clearCompleted()
      await fetchTasks()
      await fetchStats()
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function clearAllTasks() {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.clearAll()
      await fetchTasks()
      await fetchStats()
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function batchParsePending() {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.batchParsePending()
      await fetchTasks()
      await fetchStats()
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function retryFailedTasks() {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.retryFailed()
      await fetchTasks()
      await fetchStats()
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function addFile(filePath, fileType) {
    isLoading.value = true
    error.value = null
    try {
      if (fileType === 'pdf') {
        return await parseLocalFile(filePath)
      } else if (fileType === 'audio') {
        const audioStore = useAudioStore()
        const parseConfigStore = useParseConfigStore()
        const { asrModel } = parseConfigStore.audioConfig
        return await audioStore.transcribeLocalFile(filePath, asrModel)
      } else if (fileType === 'markdown') {
        ElMessage.info('Markdown 文件无需解析，可直接索引向量')
        return { success: true, message: 'Markdown 文件无需解析' }
      } else {
        throw new Error(`不支持的文件类型: ${fileType}`)
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    tasks,
    currentTask,
    stats,
    isLoading,
    error,
    tasksByState,
    pendingTasks,
    runningTasks,
    doneTasks,
    failedTasks,
    fetchTasks,
    fetchTask,
    fetchStats,
    checkDuplicate,
    parseLocalFile,
    getTaskResult,
    pollTaskUntilDone,
    getStateType,
    getStateLabel,
    clearCompletedTasks,
    clearAllTasks,
    batchParsePending,
    retryFailedTasks,
    addFile,
    clearError,
  }
})
