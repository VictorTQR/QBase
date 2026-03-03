import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ParseBackendApi } from '@/api/parseBackend'

export const useParseStore = defineStore('parse', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const stats = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchTasks(limit = 100, offset = 0) {
    isLoading.value = true
    error.value = null
    try {
      const response = await ParseBackendApi.listTasks(limit, offset)
      tasks.value = response.tasks
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTask(taskId) {
    isLoading.value = true
    error.value = null
    try {
      const task = await ParseBackendApi.getTask(taskId)
      currentTask.value = task
      return task
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await ParseBackendApi.getStats()
      return stats.value
    } catch (err) {
      console.error('获取统计信息失败:', err)
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

  function clearError() {
    error.value = null
  }

  return {
    tasks,
    currentTask,
    stats,
    isLoading,
    error,
    fetchTasks,
    fetchTask,
    fetchStats,
    checkDuplicate,
    parseLocalFile,
    getTaskResult,
    clearError,
  }
})
