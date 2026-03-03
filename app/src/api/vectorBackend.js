import { backendService as backend } from '@/utils/backend'

export class VectorBackendApi {
  static async indexDocument(params) {
    const request = backend.client.post('/api/vector/index', params)
    return await request.json()
  }

  static async searchVectors(params) {
    const request = backend.client.post('/api/vector/search', params)
    return await request.json()
  }

  static async deleteDocumentChunks(filePath) {
    const request = backend.client.delete('/api/vector/delete', {
      file_path: filePath
    })
    return await request.json()
  }

  static async getVectorStats() {
    const request = backend.client.get('/api/vector/stats')
    return await request.json()
  }

  static async clearAllVectors() {
    const request = backend.client.post('/api/vector/clear')
    return await request.json()
  }
}
