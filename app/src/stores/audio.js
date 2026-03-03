import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { AudioBackendApi } from '@/api/audioBackend'

export const useAudioStore = defineStore('audio', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const tasksByStatus = computed(() => {
    const groups = {
      pending: [],
      processing: [],
      completed: [],
      failed: [],
    }
    tasks.value.forEach((task) => {
      if (groups[task.status]) {
        groups[task.status].push(task)
      }
    })
    return groups
  })

  const pendingTasks = computed(() => tasksByStatus.value.pending)
  const processingTasks = computed(() => tasksByStatus.value.processing)
  const completedTasks = computed(() => tasksByStatus.value.completed)
  const failedTasks = computed(() => tasksByStatus.value.failed)

  async function fetchTasks() {
    isLoading.value = true
    error.value = null
    try {
      const response = await AudioBackendApi.listTasks()
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
      const task = await AudioBackendApi.getTask(taskId)
      const index = tasks.value.findIndex((t) => t.task_id === taskId)
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

  async function transcribeLocalFile(filePath, model) {
    isLoading.value = true
    error.value = null
    try {
      const result = await AudioBackendApi.transcribeLocal(filePath, model)
      await fetchTasks()
      return result
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function transcribeUploadFile(file, model) {
    isLoading.value = true
    error.value = null
    try {
      const result = await AudioBackendApi.transcribeUpload(file, model)
      await fetchTasks()
      return result
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getTaskResult(taskId) {
    try {
      return await AudioBackendApi.getTaskResult(taskId)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function deleteTask(taskId) {
    try {
      await AudioBackendApi.deleteTask(taskId)
      await fetchTasks()
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  async function pollTaskUntilDone(taskId, interval = 3000, maxAttempts = 600) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const task = await fetchTask(taskId)
      if (task.status === 'completed') {
        return { success: true, task }
      } else if (task.status === 'failed') {
        return { success: false, error: task.error || '转录失败', task }
      }
      await new Promise((resolve) => setTimeout(resolve, interval))
    }
    return { success: false, error: '超时' }
  }

  function clearError() {
    error.value = null
  }

  return {
    tasks,
    currentTask,
    isLoading,
    error,
    tasksByStatus,
    pendingTasks,
    processingTasks,
    completedTasks,
    failedTasks,
    fetchTasks,
    fetchTask,
    transcribeLocalFile,
    transcribeUploadFile,
    getTaskResult,
    deleteTask,
    pollTaskUntilDone,
    clearError,
  }
})
