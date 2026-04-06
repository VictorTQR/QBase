const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

class WorkspaceBackendApi {
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
        let errorMsg = '请求失败'
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMsg = data.detail
          } else if (Array.isArray(data.detail)) {
            errorMsg = data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
          } else {
            errorMsg = JSON.stringify(data.detail)
          }
        }
        throw new Error(errorMsg)
      }
      return data
    } catch (error) {
      console.error('Workspace API Error:', error)
      throw error
    }
  }

  async initializeWorkspace(workspacePath) {
    return this.request('/api/workspace/initialize', {
      method: 'POST',
      body: JSON.stringify({ workspace_path: workspacePath }),
    })
  }

  async checkInitialized(workspacePath) {
    return this.request(
      `/api/workspace/check-initialized?workspace_path=${encodeURIComponent(workspacePath)}`,
    )
  }

  async scanWorkspace(workspacePath, forceHash = false) {
    return this.request('/api/workspace/scan', {
      method: 'POST',
      body: JSON.stringify({
        workspace_path: workspacePath,
        force_hash: forceHash,
      }),
    })
  }
}

export const workspaceBackendApi = new WorkspaceBackendApi()
