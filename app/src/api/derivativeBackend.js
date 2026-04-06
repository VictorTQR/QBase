const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class DerivativeBackendApi {
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
      console.error('Derivative API Error:', error)
      throw error
    }
  }

  async saveDerivative(workspacePath, fileHash, derivativeType, content, options = {}) {
    const { modelUsed = null, version = 1 } = options
    return this.request('/api/derivatives/save', {
      method: 'POST',
      body: JSON.stringify({
        workspace_path: workspacePath,
        file_hash: fileHash,
        derivative_type: derivativeType,
        content,
        model_used: modelUsed,
        version,
      }),
    })
  }

  async loadDerivative(workspacePath, fileHash, derivativeType) {
    return this.request(
      `/api/derivatives/load?workspace_path=${encodeURIComponent(workspacePath)}&file_hash=${encodeURIComponent(fileHash)}&derivative_type=${encodeURIComponent(derivativeType)}`,
    )
  }

  async listDerivatives(workspacePath, fileHash) {
    return this.request(
      `/api/derivatives/list?workspace_path=${encodeURIComponent(workspacePath)}&file_hash=${encodeURIComponent(fileHash)}`,
    )
  }

  async deleteDerivative(workspacePath, fileHash, derivativeType) {
    return this.request(
      `/api/derivatives/delete?workspace_path=${encodeURIComponent(workspacePath)}&file_hash=${encodeURIComponent(fileHash)}&derivative_type=${encodeURIComponent(derivativeType)}`,
      { method: 'DELETE' },
    )
  }

  async markOutdated(workspacePath, fileHash) {
    return this.request('/api/derivatives/mark-outdated', {
      method: 'POST',
      body: JSON.stringify({
        workspace_path: workspacePath,
        file_hash: fileHash,
      }),
    })
  }
}

export const derivativeBackendApi = new DerivativeBackendApi()
