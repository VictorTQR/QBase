import hookFetch from 'hook-fetch'

const DEFAULT_BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class BackendService {
  constructor(baseUrl = DEFAULT_BACKEND_URL) {
    this.baseUrl = baseUrl
    this.client = hookFetch.create({
      baseURL: baseUrl,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }
}

class MinerUApi {
  constructor(backendService) {
    this.backend = backendService
  }

  async parseLocalFile(filePath) {
    const response = await this.backend.client.post('/api/mineru/parse-local', {
      file_path: filePath,
    })
    return response.data
  }

  async uploadAndParseFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await this.backend.client.post('/api/mineru/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async getTaskStatus(taskId) {
    const response = await this.backend.client.get(`/api/mineru/tasks/${taskId}`)
    return response.data
  }

  async getParseResult(taskId) {
    const response = await this.backend.client.get(`/api/mineru/tasks/${taskId}/result`)
    return response.data
  }

  async downloadZip(taskId) {
    const response = await this.backend.client.get(`/api/mineru/tasks/${taskId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }
}

const backendService = new BackendService()
const mineruApi = new MinerUApi(backendService)

export { backendService, mineruApi, BackendService, MinerUApi }
export default backendService
