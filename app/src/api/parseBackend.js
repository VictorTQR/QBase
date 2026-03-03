import { backendService as backend } from '@/utils/backend'

export class ParseBackendApi {
  static async checkDuplicate(params) {
    const request = backend.client.post('/api/mineru/check-duplicate', params)
    return await request.json()
  }

  static async parseFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    const request = backend.client.post('/api/mineru/parse', formData)
    return await request.json()
  }

  static async parseLocalFile(filePath) {
    const request = backend.client.post('/api/mineru/parse-local', {
      file_path: filePath,
    })
    return await request.json()
  }

  static async getTask(taskId) {
    const request = backend.client.get(`/api/mineru/tasks/${taskId}`)
    return await request.json()
  }

  static async listTasks(limit = 100, offset = 0) {
    const request = backend.client.get(`/api/mineru/tasks?limit=${limit}&offset=${offset}`)
    return await request.json()
  }

  static async getStats() {
    const request = backend.client.get('/api/mineru/stats')
    return await request.json()
  }

  static async getTaskResult(taskId) {
    const request = backend.client.get(`/api/mineru/tasks/${taskId}/result`)
    return await request.json()
  }

  static async downloadResult(taskId) {
    return backend.client.get(`/api/mineru/tasks/${taskId}/download`)
  }

  static async clearCompleted() {
    const request = backend.client.delete('/api/mineru/tasks/clear-completed')
    return await request.json()
  }

  static async clearAll() {
    const request = backend.client.delete('/api/mineru/tasks/clear-all')
    return await request.json()
  }

  static async batchParsePending() {
    const request = backend.client.post('/api/mineru/tasks/batch-parse-pending')
    return await request.json()
  }

  static async retryFailed() {
    const request = backend.client.post('/api/mineru/tasks/retry-failed')
    return await request.json()
  }
}
