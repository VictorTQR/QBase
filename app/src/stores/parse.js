import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { LocalStorageParseIndexRepository } from '@/repositories/ParseIndexRepository'
import { IndexedDBRepository } from '@/repositories/IndexedDBRepository'
import { TextExtractor } from '@/processors/parse/TextExtractor'
import { useAgentStore } from './agent'

export const useParseStore = defineStore(
  'parse',
  () => {
    const repository = new LocalStorageParseIndexRepository()
    const indexedDBRepo = new IndexedDBRepository()

    const parseIndex = ref({})
    const queue = ref([])
    const activeTask = ref(null)
    const selectedFile = ref(null)
    const showDetails = ref(false)
    const isParsing = ref(false)

    const stats = computed(() => {
      const entries = Object.values(parseIndex.value)
      return {
        total: entries.length,
        completed: entries.filter((e) => e.status === 'completed').length,
        pending: entries.filter((e) => e.status === 'pending').length,
        parsing: entries.filter((e) => e.status === 'parsing').length,
        failed: entries.filter((e) => e.status === 'failed').length,
      }
    })

    const pendingFiles = computed(() => {
      return Object.entries(parseIndex.value)
        .filter(([, data]) => data.status === 'pending')
        .map(([filePath, data]) => ({ filePath, ...data }))
    })

    const parsingFiles = computed(() => {
      return Object.entries(parseIndex.value)
        .filter(([, data]) => data.status === 'parsing')
        .map(([filePath, data]) => ({ filePath, ...data }))
    })

    const failedFiles = computed(() => {
      return Object.entries(parseIndex.value)
        .filter(([, data]) => data.status === 'failed')
        .map(([filePath, data]) => ({ filePath, ...data }))
    })

    async function loadIndex() {
      parseIndex.value = await repository.getAll()
    }

    async function addFile(filePath, type) {
      await repository.update(filePath, {
        status: 'pending',
        type,
        addedAt: Date.now(),
      })
      await loadIndex()
    }

    async function addToQueue(filePath) {
      if (!queue.value.includes(filePath)) {
        queue.value.push(filePath)
      }
    }

    async function startParsing(filePath) {
      await repository.update(filePath, {
        status: 'parsing',
        startedAt: Date.now(),
      })
      activeTask.value = filePath
      await loadIndex()
    }

    async function completeParsing(filePath, result) {
      await repository.update(filePath, {
        status: 'completed',
        completedAt: Date.now(),
        duration: result.duration || 0,
        size: result.size || 0,
      })
      activeTask.value = null
      const queueIndex = queue.value.indexOf(filePath)
      if (queueIndex > -1) {
        queue.value.splice(queueIndex, 1)
      }
      await loadIndex()
    }

    async function failParsing(filePath, error) {
      await repository.update(filePath, {
        status: 'failed',
        failedAt: Date.now(),
        error: error?.message || String(error),
      })
      activeTask.value = null
      const queueIndex = queue.value.indexOf(filePath)
      if (queueIndex > -1) {
        queue.value.splice(queueIndex, 1)
      }
      await loadIndex()
    }

    async function retryFailed() {
      const failed = Object.entries(parseIndex.value)
        .filter(([, data]) => data.status === 'failed')
        .map(([filePath]) => filePath)

      for (const filePath of failed) {
        await repository.update(filePath, {
          status: 'pending',
          error: null,
        })
      }
      await loadIndex()
    }

    async function reparse(filePath) {
      await repository.update(filePath, {
        status: 'pending',
        error: null,
      })
      await loadIndex()
    }

    async function removeFile(filePath) {
      await repository.delete(filePath)
      await loadIndex()
    }

    function selectFile(filePath) {
      selectedFile.value = filePath
      showDetails.value = true
    }

    function closeDetails() {
      showDetails.value = false
      selectedFile.value = null
    }

    async function startParse(filePath, fileType) {
      const agentStore = useAgentStore()

      try {
        isParsing.value = true

        await repository.update(filePath, {
          status: 'parsing',
          fileType,
          startedAt: Date.now(),
        })
        await loadIndex()

        const config = {
          mineru: agentStore.llmConfig.mineru,
        }

        const result = await TextExtractor.extract(filePath, fileType, config)

        await indexedDBRepo.saveExtractedText(filePath, result)

        await repository.update(filePath, {
          status: 'completed',
          fileType,
          completedAt: Date.now(),
          extractedBy: result.extractedBy,
          wordCount: result.wordCount,
          pageCount: result.pageCount,
        })

        await loadIndex()

        return result
      } catch (error) {
        console.error('解析失败:', error)

        await repository.update(filePath, {
          status: 'failed',
          fileType,
          failedAt: Date.now(),
          error: error?.message || String(error),
        })

        await loadIndex()
        throw error
      } finally {
        isParsing.value = false
      }
    }

    async function startParseBatch(fileItems) {
      const results = []

      for (const item of fileItems) {
        try {
          const result = await startParse(item.filePath, item.fileType)
          results.push({ filePath: item.filePath, success: true, result })
        } catch (error) {
          results.push({ filePath: item.filePath, success: false, error })
        }
      }

      return results
    }

    async function getExtractedText(filePath) {
      return await indexedDBRepo.getExtractedText(filePath)
    }

    loadIndex()

    return {
      parseIndex,
      queue,
      activeTask,
      selectedFile,
      showDetails,
      isParsing,
      stats,
      pendingFiles,
      parsingFiles,
      failedFiles,
      loadIndex,
      addFile,
      addToQueue,
      startParsing,
      completeParsing,
      failParsing,
      retryFailed,
      reparse,
      removeFile,
      selectFile,
      closeDetails,
      startParse,
      startParseBatch,
      getExtractedText,
    }
  },
  {
    persist: {
      key: 'qbase-parse',
      paths: ['parseIndex'],
    },
  },
)
