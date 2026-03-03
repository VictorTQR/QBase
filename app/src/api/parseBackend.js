import { backendService as backend } from '@/utils/backend'

export class ParseBackendApi {
  static async checkDuplicate(params) {
    try {
      const request = backend.client.post('/api/mineru/check-duplicate', params)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] checkDuplicate 失败:', error)
      throw new Error('去重检查失败')
    }
  }

  static async parseFile(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const request = backend.client.post('/api/mineru/parse', formData)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] parseFile 失败:', error)
      throw new Error('文件解析失败')
    }
  }

  static async parseLocalFile(filePath) {
    try {
      const request = backend.client.post('/api/mineru/parse-local', {
        file_path: filePath,
      })
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] parseLocalFile 失败:', error)
      throw new Error('本地文件解析失败')
    }
  }

  static async getTask(taskId) {
    try {
      const request = backend.client.get(`/api/mineru/tasks/${taskId}`)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] getTask 失败:', error)
      throw new Error('获取任务状态失败')
    }
  }

  static async listTasks(limit = 100, offset = 0) {
    try {
      const request = backend.client.get(`/api/mineru/tasks?limit=${limit}&offset=${offset}`)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] listTasks 失败:', error)
      throw new Error('获取任务列表失败')
    }
  }

  static async getStats() {
    try {
      const request = backend.client.get('/api/mineru/stats')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] getStats 失败:', error)
      throw new Error('获取统计数据失败')
    }
  }

  static async getTaskResult(taskId) {
    try {
      const request = backend.client.get(`/api/mineru/tasks/${taskId}/result`)
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] getTaskResult 失败:', error)
      throw new Error('获取解析结果失败')
    }
  }

  static async downloadResult(taskId) {
    try {
      return backend.client.get(`/api/mineru/tasks/${taskId}/download`)
    } catch (error) {
      console.error('[ParseBackendApi] downloadResult 失败:', error)
      throw new Error('下载结果失败')
    }
  }

  static async clearCompleted() {
    try {
      const request = backend.client.delete('/api/mineru/tasks/clear-completed')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] clearCompleted 失败:', error)
      throw new Error('清除已完成任务失败')
    }
  }

  static async clearAll() {
    try {
      const request = backend.client.delete('/api/mineru/tasks/clear-all')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] clearAll 失败:', error)
      throw new Error('清空任务失败')
    }
  }

  static async batchParsePending() {
    try {
      const request = backend.client.post('/api/mineru/tasks/batch-parse-pending')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] batchParsePending 失败:', error)
      throw new Error('批量解析失败')
    }
  }

  static async retryFailed() {
    try {
      const request = backend.client.post('/api/mineru/tasks/retry-failed')
      return await request.json()
    } catch (error) {
      console.error('[ParseBackendApi] retryFailed 失败:', error)
      throw new Error('重试失败任务失败')
    }
  }
}
