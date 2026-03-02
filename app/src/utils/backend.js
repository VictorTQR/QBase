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
    const request = this.client.get('/health')
    return await request.json()
  }
}

class MinerUApi {
  constructor(backendService) {
    this.backend = backendService
  }

  async parseLocalFile(filePath) {
    const request = this.backend.client.post('/api/mineru/parse-local', {
      file_path: filePath,
    })
    return await request.json()
  }

  async uploadAndParseFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const request = this.backend.client.post('/api/mineru/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return await request.json()
  }

  async getTaskStatus(taskId) {
    const request = this.backend.client.get(`/api/mineru/tasks/${taskId}`)
    return await request.json()
  }

  async getParseResult(taskId) {
    const request = this.backend.client.get(`/api/mineru/tasks/${taskId}/result`)
    return await request.json()
  }

  async downloadZip(taskId) {
    const request = this.backend.client.get(`/api/mineru/tasks/${taskId}/download`, {
      responseType: 'blob',
    })
    return await request.blob()
  }
}

const backendService = new BackendService()
const mineruApi = new MinerUApi(backendService)

export { backendService, mineruApi, BackendService, MinerUApi }
export default backendService
