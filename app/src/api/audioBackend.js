import { backendService as backend } from '@/utils/backend'

export class AudioBackendApi {
  static async transcribeUpload(file, model) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (model) {
        formData.append('model', model)
      }
      const request = backend.client.post('/api/audio/transcribe-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] transcribeUpload 失败:', error)
      throw new Error('音频上传转录失败')
    }
  }

  static async transcribeLocal(filePath, model) {
    try {
      const request = backend.client.post('/api/audio/transcribe-local', {
        file_path: filePath,
        model,
      })
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] transcribeLocal 失败:', error)
      throw new Error('本地音频转录失败')
    }
  }

  static async transcribe(filePath, model) {
    try {
      const request = backend.client.post('/api/audio/transcribe', {
        file_path: filePath,
        model,
      })
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] transcribe 失败:', error)
      throw new Error('音频转录失败')
    }
  }

  static async getTask(taskId) {
    try {
      const request = backend.client.get(`/api/audio/tasks/${taskId}`)
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] getTask 失败:', error)
      throw new Error('获取音频任务状态失败')
    }
  }

  static async getTaskResult(taskId) {
    try {
      const request = backend.client.get(`/api/audio/tasks/${taskId}/result`)
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] getTaskResult 失败:', error)
      throw new Error('获取音频转录结果失败')
    }
  }

  static async listTasks() {
    try {
      const request = backend.client.get('/api/audio/tasks')
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] listTasks 失败:', error)
      throw new Error('获取音频任务列表失败')
    }
  }

  static async deleteTask(taskId) {
    try {
      const request = backend.client.delete(`/api/audio/tasks/${taskId}`)
      return await request.json()
    } catch (error) {
      console.error('[AudioBackendApi] deleteTask 失败:', error)
      throw new Error('删除音频任务失败')
    }
  }
}
