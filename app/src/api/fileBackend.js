const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class FileBackendApi {
  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || '请求失败')
      }
      return data
    } catch (error) {
      console.error('File API Error:', error)
      throw error
    }
  }

  async computeHash(filePath) {
    return this.request('/api/files/hash', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath }),
    })
  }

  async listFiles(workspacePath, options = {}) {
    const { status = null, offset = 0, limit = 100 } = options
    let url = `/api/files/list?workspace_path=${encodeURIComponent(workspacePath)}&offset=${offset}&limit=${limit}`
    if (status) {
      url += `&status=${status}`
    }
    return this.request(url)
  }

  async getFile(fileHash, workspacePath = null) {
    let url = `/api/files/${fileHash}`
    if (workspacePath) {
      url += `?workspace_path=${encodeURIComponent(workspacePath)}`
    }
    return this.request(url)
  }

  async deleteFile(fileHash) {
    return this.request(`/api/files/${fileHash}`, {
      method: 'DELETE',
    })
  }
}

export const fileBackendApi = new FileBackendApi()
