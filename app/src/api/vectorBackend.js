import { backendService as backend } from '@/utils/backend'

export class VectorBackendApi {
  static async indexDocument(params) {
    console.log('[VectorBackendApi] indexDocument 调用，参数:', params)
    try {
      const request = backend.client.post('/api/vector/index', params)
      const response = await request
      console.log('[VectorBackendApi] 响应状态:', response.status)
      const result = await response.json()
      console.log('[VectorBackendApi] 响应数据:', result)
      return result
    } catch (error) {
      console.error('[VectorBackendApi] 请求失败:', error)
      if (error.response) {
        console.error('[VectorBackendApi] 错误响应状态:', error.response.status)
        try {
          const errorData = await error.response.json()
          console.error('[VectorBackendApi] 错误响应数据:', errorData)
          throw new Error(errorData.detail || errorData.message || '索引请求失败')
        } catch (e) {
          console.error('[VectorBackendApi] 解析错误响应失败:', e)
          throw new Error(`索引请求失败 (${error.response.status})`)
        }
      }
      throw error
    }
  }

  static async searchVectors(params) {
    console.log('[VectorBackendApi] searchVectors 调用，参数:', params)
    try {
      const request = backend.client.post('/api/vector/search', params)
      return await request.json()
    } catch (error) {
      console.error('[VectorBackendApi] searchVectors 失败:', error)
      if (error.response) {
        try {
          const errorData = await error.response.json()
          throw new Error(errorData.detail || errorData.message || '向量搜索失败')
        } catch (e) {
          throw new Error(`向量搜索失败 (${error.response.status})`)
        }
      }
      throw error
    }
  }

  static async deleteDocumentChunks(filePath) {
    console.log('[VectorBackendApi] deleteDocumentChunks 调用，filePath:', filePath)
    const request = backend.client.delete('/api/vector/delete', {
      file_path: filePath,
    })
    return await request.json()
  }

  static async getVectorStats() {
    console.log('[VectorBackendApi] getVectorStats 调用')
    const request = backend.client.get('/api/vector/stats')
    return await request.json()
  }

  static async clearAllVectors() {
    console.log('[VectorBackendApi] clearAllVectors 调用')
    const request = backend.client.post('/api/vector/clear')
    return await request.json()
  }
}
