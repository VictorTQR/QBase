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
    const indexedFiles = ref({})

    async function indexDocument(filePath, fileName, content, workspaceId, taskId) {
      isIndexing.value = true
      currentIndexingFile.value = fileName
      error.value = null

      const requestParams = {
        file_path: filePath,
        file_name: fileName,
        workspace_id: workspaceId || '',
      }

      if (taskId) {
        requestParams.task_id = taskId
        console.log('[VectorStore] 使用 task_id 索引:', taskId)
      } else {
        requestParams.content = content
        console.log('[VectorStore] 使用 content 索引，长度:', content?.length || 0)
      }

      console.log('[VectorStore] 准备索引文档，请求参数:', requestParams)
      console.log('[VectorStore] workspace_id (处理后):', requestParams.workspace_id)

      try {
        const result = await VectorBackendApi.indexDocument(requestParams)
        console.log('[VectorStore] 索引成功:', result)
        indexedFiles.value[filePath] = true
        await loadStats()
        return result
      } catch (err) {
        console.error('[VectorStore] 索引失败:', err)
        console.error('[VectorStore] 错误详情:', {
          message: err.message,
          response: err.response,
          status: err.status,
        })
        error.value = err.message
        throw err
      } finally {
        isIndexing.value = false
        currentIndexingFile.value = ''
      }
    }

    async function indexBatch(tasks, getExtractedTextFn, workspaceId = null) {
      isIndexing.value = true
      indexingProgress.value = 0
      indexingTotal.value = tasks.length
      error.value = null
      const results = []
      const failed = []

      try {
        for (let i = 0; i < tasks.length; i++) {
          const task = tasks[i]
          currentIndexingFile.value = task.file_name
          indexingProgress.value = i + 1

          try {
            const result = await indexDocument(
              task.file_path,
              task.file_name,
              null,
              workspaceId,
              task.id,
            )
            results.push({ task, result })
          } catch (err) {
            failed.push({ task, error: err.message })
          }
        }

        await loadStats()
        return { success: true, results, failed }
      } catch (err) {
        error.value = err.message
        throw err
      } finally {
        isIndexing.value = false
        indexingProgress.value = 0
        indexingTotal.value = 0
        currentIndexingFile.value = ''
      }
    }

    function isFileIndexed(filePath) {
      return !!indexedFiles.value[filePath]
    }

    function markFileIndexed(filePath) {
      indexedFiles.value[filePath] = true
    }

    function unmarkFileIndexed(filePath) {
      delete indexedFiles.value[filePath]
    }

    async function searchVectors(query, topK = 10, workspaceId = null) {
      return await VectorBackendApi.searchVectors({
        query,
        top_k: topK,
        workspace_id: workspaceId,
      })
    }

    async function deleteDocumentChunks(filePath) {
      const result = await VectorBackendApi.deleteDocumentChunks(filePath)
      unmarkFileIndexed(filePath)
      await loadStats()
      return result
    }

    async function loadStats() {
      stats.value = await VectorBackendApi.getVectorStats()
      return stats.value
    }

    async function clearAll() {
      const result = await VectorBackendApi.clearAllVectors()
      stats.value = null
      indexedFiles.value = {}
      return result
    }

    return {
      isIndexing,
      indexingProgress,
      indexingTotal,
      currentIndexingFile,
      error,
      stats,
      indexedFiles,
      indexDocument,
      indexBatch,
      isFileIndexed,
      markFileIndexed,
      unmarkFileIndexed,
      searchVectors,
      deleteDocumentChunks,
      loadStats,
      clearAll,
    }
  },
  {
    persist: {
      key: 'qbase-vector',
      paths: ['indexedFiles'],
    },
  },
)
