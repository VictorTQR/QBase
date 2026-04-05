import { backendService as backend } from '@/utils/backend'

/**
 * Papers API 客户端
 * 提供与后端论文 API 的交互方法
 */
export class PapersBackendApi {
  /**
   * 搜索 arXiv 论文
   * @param {string} keyword - 搜索关键词
   * @param {number} maxResults - 最大结果数（默认10）
   * @param {string} sortBy - 排序方式：'relevance' | 'lastUpdatedDate' | 'submittedDate'（默认'relevance'）
   * @returns {Promise<Object>} 搜索结果
   */
  static async searchPapers(keyword, maxResults = 10, sortBy = 'relevance') {
    console.log('[PapersBackendApi] searchPapers 调用，参数:', { keyword, maxResults, sortBy })
    try {
      const request = backend.client.post('/api/papers/search', {
        keyword,
        max_results: maxResults,
        sort_by: sortBy,
      })
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] searchPapers 失败:', error)
      throw new Error('搜索论文失败')
    }
  }

  /**
   * 保存搜索结果到数据库
   * @param {string} keyword - 搜索关键词
   * @param {number} maxResults - 最大结果数（默认10）
   * @param {string} sortBy - 排序方式：'relevance' | 'lastUpdatedDate' | 'submittedDate'（默认'relevance'）
   * @returns {Promise<Object>} 保存结果
   */
  static async savePapers(keyword, maxResults = 10, sortBy = 'relevance') {
    console.log('[PapersBackendApi] savePapers 调用，参数:', { keyword, maxResults, sortBy })
    try {
      const request = backend.client.post('/api/papers/save', {
        keyword,
        max_results: maxResults,
        sort_by: sortBy,
      })
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] savePapers 失败:', error)
      throw new Error('保存论文失败')
    }
  }

  /**
   * 获取已保存的论文列表
   * @param {number} offset - 偏移量（默认0）
   * @param {number} limit - 限制数量（默认50）
   * @returns {Promise<Object>} 论文列表
   */
  static async getPaperList(offset = 0, limit = 50) {
    console.log('[PapersBackendApi] getPaperList 调用，参数:', { offset, limit })
    try {
      const request = backend.client.get(`/api/papers/list?offset=${offset}&limit=${limit}`)
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] getPaperList 失败:', error)
      throw new Error('获取论文列表失败')
    }
  }

  /**
   * 获取论文统计信息
   * @returns {Promise<Object>} 统计信息
   */
  static async getPaperStats() {
    console.log('[PapersBackendApi] getPaperStats 调用')
    try {
      const request = backend.client.get('/api/papers/stats')
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] getPaperStats 失败:', error)
      throw new Error('获取论文统计信息失败')
    }
  }
}
