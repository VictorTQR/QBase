import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { PapersBackendApi } from '@/api/papers'

export const usePapersStore = defineStore('papers', () => {
  const papers = ref([])
  const stats = ref(null)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const loading = ref(false)
  const searchResults = ref([])
  const searchLoading = ref(false)

  const hasPapers = computed(() => papers.value.length > 0)

  async function fetchPapers(page = currentPage.value, size = pageSize.value) {
    try {
      loading.value = true
      currentPage.value = page
      pageSize.value = size
      const offset = (page - 1) * size
      const result = await PapersBackendApi.getPaperList(offset, size)

      if (result.success) {
        papers.value = result.data?.papers || []
        total.value = result.data?.total || 0
      }
      return result
    } catch (error) {
      console.error('[PapersStore] fetchPapers failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function searchPapers(keyword, maxResults = 10, sortBy = 'relevance') {
    try {
      searchLoading.value = true
      const result = await PapersBackendApi.searchPapers(keyword, maxResults, sortBy)

      if (result.success) {
        searchResults.value = result.data?.papers || []
      }
      return result
    } catch (error) {
      console.error('[PapersStore] searchPapers failed:', error)
      throw error
    } finally {
      searchLoading.value = false
    }
  }

  async function savePapers(keyword, maxResults = 10, sortBy = 'relevance') {
    try {
      const result = await PapersBackendApi.savePapers(keyword, maxResults, sortBy)

      if (result.success) {
        await fetchPapers()
        await fetchStats()
      }
      return result
    } catch (error) {
      console.error('[PapersStore] savePapers failed:', error)
      throw error
    }
  }

  async function deletePaper(entryId) {
    try {
      const result = await PapersBackendApi.deletePaper(entryId)

      if (result.success) {
        await fetchPapers()
        await fetchStats()
      }
      return result
    } catch (error) {
      console.error('[PapersStore] deletePaper failed:', error)
      throw error
    }
  }

  async function fetchStats() {
    try {
      const result = await PapersBackendApi.getPaperStats()

      if (result.success) {
        stats.value = result.data
      }
      return result
    } catch (error) {
      console.error('[PapersStore] fetchStats failed:', error)
      throw error
    }
  }

  function clearSearchResults() {
    searchResults.value = []
  }

  function setCurrentPage(page) {
    currentPage.value = page
  }

  function setPageSize(size) {
    pageSize.value = size
    currentPage.value = 1
  }

  return {
    papers,
    stats,
    currentPage,
    pageSize,
    total,
    loading,
    searchResults,
    searchLoading,
    hasPapers,
    fetchPapers,
    searchPapers,
    savePapers,
    deletePaper,
    fetchStats,
    clearSearchResults,
    setCurrentPage,
    setPageSize,
  }
})
