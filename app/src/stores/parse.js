import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { LocalStorageParseIndexRepository } from '@/repositories/ParseIndexRepository'

export const useParseStore = defineStore(
  'parse',
  () => {
    const repository = new LocalStorageParseIndexRepository()

    const parseIndex = ref({})
    const queue = ref([])
    const activeTask = ref(null)
    const selectedFile = ref(null)
    const showDetails = ref(false)

    const stats = computed(() => {
      const entries = Object.values(parseIndex.value)
      return {
        total: entries.length,
        completed: entries.filter(e => e.status === 'completed').length,
        pending: entries.filter(e => e.status === 'pending').length,
        parsing: entries.filter(e => e.status === 'parsing').length,
        failed: entries.filter(e => e.status === 'failed').length,
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
        addedAt: Date.now()
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
        startedAt: Date.now()
      })
      activeTask.value = filePath
      await loadIndex()
    }

    async function completeParsing(filePath, result) {
      await repository.update(filePath, {
        status: 'completed',
        completedAt: Date.now(),
        duration: result.duration || 0,
        size: result.size || 0
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
        error: error?.message || String(error)
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
          error: null
        })
      }
      await loadIndex()
    }

    async function reparse(filePath) {
      await repository.update(filePath, {
        status: 'pending',
        error: null
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

    loadIndex()

    return {
      parseIndex,
      queue,
      activeTask,
      selectedFile,
      showDetails,
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
      closeDetails
    }
  },
  {
    persist: {
      key: 'qbase-parse',
      paths: ['parseIndex'],
    },
  }
)
