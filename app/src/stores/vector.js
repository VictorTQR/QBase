import { ref } from 'vue'
import { defineStore } from 'pinia'
import { VectorBackendApi } from '@/api/vectorBackend'

export const useVectorStore = defineStore(
  'vector',
  () => {
    const isIndexing = ref(false)
    const indexingProgress = ref(0)
    const indexingTotal = ref(0)
    const currentIndexingFile = ref('')
    const error = ref(null)
    const stats = ref(null)

    async function indexDocument(filePath, fileName, content, workspaceId) {
      isIndexing.value = true
      currentIndexingFile.value = fileName
      error.value = null

      try {
        const result = await VectorBackendApi.indexDocument({
          file_path: filePath,
          file_name: fileName,
          content,
          workspace_id: workspaceId
        })
        await loadStats()
        return result
      } catch (err) {
        error.value = err.message
        throw err
      } finally {
        isIndexing.value = false
        currentIndexingFile.value = ''
      }
    }

    async function searchVectors(query, topK = 10, workspaceId = null) {
      return await VectorBackendApi.searchVectors({
        query,
        top_k: topK,
        workspace_id: workspaceId
      })
    }

    async function deleteDocumentChunks(filePath) {
      return await VectorBackendApi.deleteDocumentChunks(filePath)
    }

    async function loadStats() {
      stats.value = await VectorBackendApi.getVectorStats()
      return stats.value
    }

    async function clearAll() {
      const result = await VectorBackendApi.clearAllVectors()
      stats.value = null
      return result
    }

    return {
      isIndexing,
      indexingProgress,
      indexingTotal,
      currentIndexingFile,
      error,
      stats,
      indexDocument,
      searchVectors,
      deleteDocumentChunks,
      loadStats,
      clearAll
    }
  },
  {
    persist: {
      key: 'qbase-vector',
      paths: []
    }
  }
)
